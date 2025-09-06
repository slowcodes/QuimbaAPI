from models.lab.lab import LabService, Experiment, LabServiceExperiment, ExperimentParameter, ParameterType, \
    ExperimentParameterBounds, BoundaryType


def insert_params(session, data):
    # Step 1: Fetch all LabService records
    lab_services = session.query(LabService).all()
    lab_service_ids = {service.id for service in lab_services}

    # Step 2: Process each LabService
    for lab_service in lab_services:
        # Fetch associated parameters from JSON
        parameters = [entry for entry in data if entry["lab_test_id"] == lab_service.id]

        # If no parameters exist for this LabService, skip it
        if not parameters:
            print(f"No parameters found for LabService ID {lab_service.id}, skipping...")
            continue

        # Step 3: Create Default Experiment for this LabService
        experiment = Experiment(description="Investigation Methodology")
        session.add(experiment)
        session.flush()  # Ensure experiment ID is available

        # Step 4: Link Experiment to LabService
        lab_service_exp = LabServiceExperiment(
            lab_service_id=lab_service.id,
            experiment_id=experiment.id
        )
        session.add(lab_service_exp)

        # Step 5: Insert Parameters & Boundaries
        for param in parameters:
            # Create ExperimentParameter entry
            param_entry = ExperimentParameter(
                parameter=param["parameter"],
                measuring_unit=param["unit"],
                parameter_type=ParameterType.Description if param[
                                                                "value_data_type"] == "Text" else ParameterType.Number,
                exp_id=experiment.id
            )
            session.add(param_entry)
            session.flush()  # Get parameter ID

            # Step 6: Create Boundary if min or max > 0
            if param["min"] > 0 or param["max"] > 0:
                bounds_entry = ExperimentParameterBounds(
                    parameter_id=param_entry.id,
                    lower_bound=param["min"],
                    upper_bound=param["max"],
                    boundary_type=BoundaryType.Normal  # Assuming normal range
                )
                session.add(bounds_entry)
            print("Processing Parameter: ", param["parameter"])
    # Commit all changes
    session.commit()


print("Data successfully inserted into the database!")
