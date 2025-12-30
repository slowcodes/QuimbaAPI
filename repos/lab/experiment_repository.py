import decimal
from decimal import Decimal
from http.client import HTTPException

from sqlalchemy.orm import Session

from dtos.lab import ExperimentResultReadingDTO, ParameterBoundaryDTO, ExpDTO, ExperimentParameterDTO
from models.lab.lab import ExperimentParameterBounds, ExperimentResultReading, ExperimentParameter, Experiment, \
    LabServiceExperiment


class ExperimentRepository:
    def __init__(self, db_session: Session):
        self.session = db_session

    def create_reading(self, result: ExperimentResultReadingDTO) -> ExperimentResultReadingDTO:
        reading = ExperimentResultReading(
            result_id=result.result_id,
            parameter_id=result.parameter_id,
            parameter_value=result.parameter_value
        )
        self.session.add(reading)
        self.session.commit()
        self.session.refresh(reading)

        return {
            'id': reading.id,
            'result_id': reading.result_id,
            'parameter_id': reading.parameter_id,
            'parameter_value': reading.parameter_value,
            'created_at': reading.created_at
        }

    def get_parameter_boundaries(self, parameter_id):
        bound_query = self.session.query(ExperimentParameterBounds) \
            .filter(ExperimentParameterBounds.parameter_id == parameter_id).all()

        bounds = []
        for bound in bound_query:
            bounds.append({
                'boundary_id': bound.id,
                'parameter_id': bound.parameter_id,
                'upper_bound': bound.upper_bound,
                'lower_bound': bound.lower_bound,
                'boundary_type': bound.boundary_type,
            })
        return bounds

    def reading_exits(self, result: ExperimentResultReadingDTO) -> bool:
        exist = self.session.query(ExperimentResultReading) \
            .filter(ExperimentResultReading.result_id == result.result_id) \
            .filter(ExperimentResultReading.parameter_id == result.parameter_id).first()

        if exist:
            return True

        return False

    def get_reading_by_id(self, reading_id: int):
        return self.session.query(ExperimentResultReading).filter(ExperimentResultReading.id == reading_id).first()

    def delete_experiment_reading_result_id(self, result_id):
        readings = self.session.query(ExperimentResultReading).filter(ExperimentResultReading.result_id == result_id).all()

        if readings is not None:
            for reading in readings:
                self.session.delete(reading)
                self.session.commit()
            return True  # readings were found and deleted
        else:
            return False  # no reading found

    def get_experiment_parameter(self, exp_id: int):
        cols = [
            ExperimentParameter.id,
            ExperimentParameter.parameter,
            ExperimentParameter.measuring_unit,
            ExperimentParameter.parameter_type,
        ]
        rs = self.session.query(*cols).select_from(ExperimentParameter).filter(
            ExperimentParameter.exp_id == exp_id).all()
        parameter = []
        for param in rs:
            parameter.append({
                'boundary': self.get_parameter_boundaries(param.id),
                'name': param.parameter,
                'unit': param.measuring_unit,
                'type': param.parameter_type,
                'paramKey': param.id
            })
        return parameter

    def get_lab_experiments(self, lab_service_id: int):
        cols = [
            Experiment.id,
            Experiment.description,
            LabServiceExperiment.lab_service_id.label("service_id")
        ]

        rs = self.session.query(*cols).select_from(Experiment) \
            .join(LabServiceExperiment, Experiment.id == LabServiceExperiment.experiment_id) \
            .filter(LabServiceExperiment.lab_service_id == lab_service_id).all()

        rtn = []
        for items in rs:
            rtn.append(
                {
                    'name': items.description,
                    'key': items.id,
                    'parameter': self.get_experiment_parameter(items.id)
                })

        return rtn

    def update_experiment(self, lab_service_id: int, exp: ExpDTO):
        """ Updates or creates an experiment and its parameters. """

        experiment = ''
        if exp.id is None:
            # If exp.key is None, create a new experiment with the name as description
            experiment = Experiment(description=exp.description)
            self.session.add(experiment)  # Only add if it's a new experiment
            self.session.flush()  # Ensure the experiment has an ID before linking it

            # Add the LabServiceExperiment association only when a new experiment is created
            new_lab_exp = LabServiceExperiment(lab_service_id=lab_service_id, experiment_id=experiment.id)
            self.session.add(new_lab_exp)

        else:
            # If exp.key is not None, try to find the existing experiment
            experiment = self.session.query(Experiment).filter(Experiment.id == exp.id).first()
            print('update exp', experiment)
            if not experiment:
                # If experiment is not found, create a new one
                experiment = Experiment(description=exp.description)
                self.session.add(experiment)  # Only add if it's a new experiment
                self.session.flush()  # Ensure the experiment has an ID before linking it

                # Add the LabServiceExperiment association only when a new experiment is created
                # TODO: check if this is needed or will cause duplicate entries
                new_lab_exp = LabServiceExperiment(lab_service_id=lab_service_id, experiment_id=experiment.id)
                self.session.add(new_lab_exp)
            else:
                # If found, update the existing experiment's attributes (NO db.add here)
                experiment.description = exp.description
                self.session.add(experiment)
                print('update exp II', exp.description)  # Add the existing experiment to the session
                # Here, no need to call db.add() since it's already in the session

        # Update parameters for the experiment
        allowed_params = []
        for param in exp.parameters:
            updated_param_id = self.update_parameter(experiment.id, param)
            allowed_params.append(updated_param_id)

        # Remove parameters that are no longer associated with the experiment
        self.session.query(ExperimentParameter).filter(ExperimentParameter.exp_id == experiment.id,
                                                       ~ExperimentParameter.id.in_(allowed_params)).delete(
            synchronize_session=False)

        self.session.commit()  # Commit to persist all changes

    def update_parameter(self, exp_id: int, param: ExperimentParameterDTO):
        """ Updates a single experiment parameter and its boundaries. """
        existing_param = self.session.query(ExperimentParameter).filter(
            ExperimentParameter.id == param.id
        ).first()

        if existing_param:
            existing_param.parameter = param.parameter
            existing_param.measuring_unit = param.measuring_unit
            existing_param.parameter_type = param.parameter_type
            param_id = existing_param.id

            self.session.commit()

        else:
            new_param = ExperimentParameter(
                parameter=param.parameter,
                measuring_unit=param.measuring_unit,
                parameter_type=param.parameter_type,
                exp_id=exp_id
            )
            self.session.add(new_param)
            self.session.flush()  # Ensure new_param has an ID before adding boundaries
            param_id = new_param.id  # Assign new ID

        # Update boundaries
        allowed_boundaries = []
        for boundary in param.boundary:
            updated_boundary = self.update_parameter_boundary(param_id, boundary)
            allowed_boundaries.append(updated_boundary)

        # Remove boundaries that are no longer associated with the parameter
        self.session.query(ExperimentParameterBounds).filter(ExperimentParameterBounds.parameter_id == param_id,
                                                             ~ExperimentParameterBounds.id.in_(
                                                                 allowed_boundaries)).delete(synchronize_session=False)

        self.session.commit()
        return param_id

    def update_parameter_boundary(self, parameter_id: int, boundary: ParameterBoundaryDTO):
        """ Updates a single boundary for a given experiment parameter. """

        self.session.query(ExperimentParameterBounds).filter(
            ExperimentParameterBounds.parameter_id == parameter_id and ExperimentParameterBounds.id == boundary.boundary_id
        ).delete()

        """ 
        boundaries can be removed and replace without any issue
        because only the experiment parameter id is linked to a boundary
        this will not affect existing reading. It only changes how the reading is interpreted
        """
        new_boundary = ExperimentParameterBounds(
            parameter_id=parameter_id,
            upper_bound=boundary.upper_bound,
            lower_bound=boundary.lower_bound,
            boundary_type=boundary.boundary_type
        )
        self.session.add(new_boundary)
        self.session.flush()
        return new_boundary.id
