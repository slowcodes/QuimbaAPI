from dtos.auth import UserDTO
from dtos.pharmacy.prescription import PrescriptionDTO, PrescriptionDetailDTO
from models.pharmacy import Prescription, PrescriptionStatus, PrescriptionDetail, Form
from repos.auth_repository import UserRepository
from repos.base_repository import BaseRepository
from repos.client.client_repository import ClientRepository
from repos.consultation.consultant_repository import ConsultantRepository
from repos.pharmacy.drug_repository import DrugRepository
from repos.pharmacy.pharmacy_repository import PharmacyRepository


class PrescriptionRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db)
        self.consultation_repository = ConsultantRepository(db)
        self.client_repository = ClientRepository(db)
        self.auth_repository = UserRepository(db)
        self.pharmacy_repository = PharmacyRepository(db)
        self.drug_repository = DrugRepository(db)

    def get_all(self, skip: int = 0, limit: int = 0, status: PrescriptionStatus = PrescriptionStatus.All,
                start_date: str = None, end_date: str = None):
        query = self.db.query(Prescription)

        if status != PrescriptionStatus.All:
            query = query.filter(Prescription.status == status)

        if start_date and end_date:
            query = query.filter(Prescription.created_at.between(start_date, end_date))

        query = query.offset(skip).limit(limit).all()
        prescriptions = []
        for prescription in query:
            self.consultation_repository.get_consultant_by_id(
                prescription.consultant_id) if prescription.consultant_id else None

            consultant_specialist = self.consultation_repository.get_consultant_by_id(prescription.consultant_id)
            prescriptions.append(
                {
                    'id': prescription.id,
                    'status': prescription.status,
                    'note': prescription.note,
                    'instruction': prescription.instruction,
                    'created_at': (prescription.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                    'client': self.client_repository.get_client(
                        prescription.client_id) if prescription.client_id else None,
                    'consultant': {
                        'title': "Professor",  # consultant_specialist.title,
                        'id': prescription.consultant_id,
                        'user': self.auth_repository.get_usr_by_id(1)
                    },
                    'pharmacy': self.pharmacy_repository.get_pharmacy_by_id(prescription.pharmacy_id),
                    'prescriptions': self.get_prescription_details(prescription.id)
                })
        return prescriptions

    def get_prescription_details(self, prescription_id: int):
        dts = self.db.query(PrescriptionDetail).filter(PrescriptionDetail.prescription_id == prescription_id).all()
        details = []
        for prescription in dts:
            details.append(
                {
                    'id': prescription.id,
                    'drug': self.drug_repository.get(prescription.drug_id),
                    'form': Form(prescription.form).name,
                    'frequency': prescription.frequency,
                    'weight_volume': prescription.weight_volume,
                    'dosage': prescription.dosage,
                    'interval': prescription.interval,
                    'duration': prescription.duration,
                    'is_prn': prescription.is_prn,
                    'status': prescription.status.name
                }
            )
        return details

    def create(self, prescription_dto: PrescriptionDTO, user: UserDTO) -> PrescriptionDTO:

        prescription = prescription_dto.dict()
        consultant = self.consultation_repository.get_consultant_by_user_id(user.id)

        psd = prescription.pop("prescriptions")

        prescription = self.add(
            Prescription(
                consultant_id=consultant.id if consultant else 1,
                pharmacy_id=prescription_dto.pharmacy_id,
                client_id=prescription_dto.client.id if prescription_dto.client else None,
                status=PrescriptionStatus.Pending,
                instruction=prescription_dto.instruction,
                note=prescription_dto.note,
            ))

        self.db.flush(prescription)
        ps = PrescriptionDTO(
            id=prescription.id,
            status=prescription.status,
            note=prescription.note,
            instruction=prescription.instruction,
            pharmacy_id=prescription.pharmacy_id,
            created_at=(prescription.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            client=prescription_dto.client,
            consultant=prescription_dto.consultant if prescription_dto.consultant else None,
        )

        pres = []
        for item in psd:
            dg = item["drug"]
            dg = dg["drug_info"]
            prescription_item = self.add(
                PrescriptionDetail(
                    drug_id=dg["id"],
                    prescription_id=prescription.id,
                    form=item["form"],
                    frequency=item["frequency"],
                    weight_volume=item["weight_volume"],
                    dosage=item["dosage"],
                    interval=item["interval"],
                    duration=item["duration"],
                    is_prn=item.get("is_prn"),
                    status=PrescriptionStatus.Pending
                )
            )

            pres.append(
                PrescriptionDetailDTO.from_orm(prescription_item)
            )

        ps.prescriptions = pres

        return ps
