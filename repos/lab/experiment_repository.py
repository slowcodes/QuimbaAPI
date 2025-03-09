from sqlalchemy.orm import Session

from commands.lab import ExperimentResultReadingDTO
from models.lab.lab import ExperimentParameterBounds, ExperimentResultReading, ExperimentParameter


class ExperimentResultReadingRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_reading(self, result: ExperimentResultReadingDTO) -> ExperimentResultReadingDTO:
        reading = ExperimentResultReading(
            sample_id=result.sample_id,
            parameter_id=result.parameter_id,
            parameter_value=result.parameter_value
        )
        self.db_session.add(reading)
        self.db_session.commit()
        self.db_session.refresh(reading)
        return {
            'id': reading.id,
            'sample_id': reading.sample_id,
            'parameter_id': reading.parameter_id,
            'parameter_value': reading.parameter_value,
            'created_at': reading.created_at
        }

    def get_parameter_boundaries(self, parameter_id):
        bound_query = self.db_session.query(ExperimentParameterBounds) \
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
        exist = self.db_session.query(ExperimentResultReading) \
            .filter(ExperimentResultReading.sample_id == result.sample_id) \
            .filter(ExperimentResultReading.parameter_id == result.parameter_id).first()

        if exist:
            return True

        return False

    def get_reading_by_id(self, reading_id: int):
        return self.db_session.query(ExperimentResultReading).filter(ExperimentResultReading.id == reading_id).first()

    def get_readings_sample_id(self, sample_id: int):
        return self.db_session.query(ExperimentResultReading).filter(ExperimentResultReading.sample_id == sample_id).all()

    def get_readings_by_sample_id(self, sample_id: int):

        cols = [
            ExperimentResultReading.id,
            ExperimentResultReading.sample_id,
            ExperimentResultReading.created_at,
            ExperimentResultReading.parameter_id,
            ExperimentResultReading.parameter_value,
            ExperimentResultReading.id.label("exp_reading_id"),
            ExperimentParameter.parameter,
            ExperimentParameter.parameter_type,
            ExperimentParameter.measuring_unit,
        ]
        query = self.db_session.query(*cols).select_from(ExperimentResultReading)\
            .join(ExperimentParameter, ExperimentParameter.id == ExperimentResultReading.parameter_id) \
            .filter(ExperimentResultReading.sample_id == sample_id).all()

        readings = []
        for reading in query:
            readings.append({
                'id': reading.id,
                'sample_id': reading.sample_id,
                'parameter_id': reading.parameter_id,
                'parameter_value': reading.parameter_value,
                'created_at': reading.created_at,
                'parameter': reading.parameter,
                'parameter_type': reading.parameter_type,
                'measuring_unit': reading.measuring_unit,
                'parameter_boundaries': self.get_parameter_boundaries(reading.parameter_id)
            })

        return readings

    def delete_experiment_reading_sample_id(self, sample_id):
        readings = self.get_readings_sample_id(sample_id)

        if readings is not None:
            for reading in readings:
                self.db_session.delete(reading)
                self.db_session.commit()
            return True # readings were found and deleted
        else:
            return False # no reading found
