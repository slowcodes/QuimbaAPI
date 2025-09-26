from datetime import datetime
from typing import Optional

from models.product import Product, PackagingType

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Date,
    Enum as SqlEnum,
    Double, Text, Index, DateTime, BIGINT,
)
from sqlalchemy.orm import relationship, backref, Mapped, mapped_column
from db import Base
from enum import Enum

from models.mixins import SoftDeleteMixin


# Enums
class Form(str, Enum):
    Tablet = 'Tablet'
    Capsule = 'Capsule'
    Syrup = 'Syrup'
    Suspension = 'Suspension'
    Solution = 'Solution'
    Injection = 'Injection'
    Cream = 'Cream'
    Ointment = 'Ointment'
    Gel = 'Gel'
    Lotion = 'Lotion'
    Patch = 'Patch'
    Suppository = 'Suppository'
    Powder = 'Powder'
    Lozenge = 'Lozenge'
    Spray = 'Spray'
    Drop = 'Drop'
    Inhaler = 'Inhaler'
    Granule = 'Granule'
    Foam = 'Foam'
    Enema = 'Enema'


class Route(str, Enum):
    Oral = 'Oral'
    Intravenous = 'Intravenous'
    Intramuscular = 'Intramuscular'
    Subcutaneous = 'Subcutaneous'
    Topical = 'Topical'
    Rectal = 'Rectal'
    Nasal = 'Nasal'
    Sublingual = 'Sublingual'
    Inhalation = 'Inhalation'
    Ophthalmic = 'Ophthalmic'
    Otic = 'Otic'
    Vaginal = 'Vaginal'
    Transdermal = 'Transdermal'


# Base model with soft delete


class Pharmacy(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy"
    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=True)
    org_id = Column(Integer, ForeignKey("organization.id", ondelete="cascade"))

    children = relationship(
        "PharmacyHierarchy", foreign_keys="[PharmacyHierarchy.parent_id]", backref="parent_pharmacy"
    )
    parents = relationship(
        "PharmacyHierarchy", foreign_keys="[PharmacyHierarchy.pharmacy_id]", backref="child_pharmacy"
    )


class PharmacyHierarchy(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_hierarchy"
    id = Column(Integer, primary_key=True, index=True)
    pharmacy_id = Column(Integer, ForeignKey("pharmacy.id", ondelete="cascade"))
    parent_id = Column(Integer, ForeignKey("pharmacy.id", ondelete="cascade"))


class DrugGroup(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_drug_category"
    id = Column(Integer, primary_key=True, index=True)
    group = Column(String(100), nullable=False, unique=True)
    use = Column(String(300), nullable=True)
    parent_id = Column(Integer, ForeignKey("pharmacy_drug_category.id", ondelete="cascade"))

    parent = relationship("DrugGroup", remote_side=[id], backref=backref("children", lazy="dynamic"))
    tags = relationship("DrugGroupTag", back_populates="group", cascade="all, delete-orphan")


class DrugGroupTag(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_drug_category_tag"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("pharmacy_drug_category.id", ondelete="cascade"))
    drug_id = Column(Integer, ForeignKey("pharmacy_drug.id", ondelete="cascade"))

    group = relationship("DrugGroup", back_populates="tags")
    drug = relationship("Drug", back_populates="group_tags")


class Drug(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_drug"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="cascade"))

    active_ingredients = Column(Text)  # Active ingredients in the drug
    storage_conditions = Column(String(255))  # Storage conditions
    warnings = Column(Text)  # Warnings or precautions for use
    interactions = Column(Text)  # Potential drug interactions
    contraindications = Column(Text)  # Contraindications for use
    side_effects = Column(Text)  # Common or rare side effects # List of dosage forms (tablet, injection, etc.)
    drug_image_url = Column(String(255))  # URL of the drug image
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="pharmacy_drug")
    group_tags = relationship("DrugGroupTag", back_populates="drug")

    allergies = relationship("DrugAllergy", back_populates="drug", cascade="all, delete-orphan")



class PharmacyDrugMovement(Base):
    __tablename__ = "pharmacy_drug_movement"
    id = Column(Integer, primary_key=True, index=True)
    drug_form = Column(SqlEnum(Form))
    drug_id = Column(Integer, ForeignKey("pharmacy_drug.id", ondelete="cascade"))
    package_type = Column(Integer, ForeignKey("product_package.id", ondelete="cascade"))
    quantity = Column(Integer)
    moved_at = Column(DateTime, default=datetime.utcnow)
    transaction_id = Column(BIGINT, ForeignKey("transaction.id", ondelete="cascade"))


class DrugForm(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_drug_form"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    drug_form = Column(SqlEnum(Form))
    drug_id = Column(Integer, ForeignKey("pharmacy_drug.id", ondelete="cascade"))


class PharmDrugFormPackage(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_drug_form_package"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    form_id = Column(Integer, ForeignKey("pharmacy_drug_form.id", ondelete="cascade"))
    package_container = Column(SqlEnum(PackagingType))
    sales_price_code_id = Column(Integer, ForeignKey("sales_price_code.id", ondelete="cascade"))
    # parent_package_id: Mapped[Optional[int]] = mapped_column(ForeignKey('pharm_drug_form_package.id'))

    product_barcode = relationship("Barcode", back_populates="pharmacy_drug_form_package")
    # sales_price_code = relationship("SalesPriceCode", back_populates="pharmacy_drug_form_package")
    # sales = relationship("BusinessSales", back_populates="pharmacy_drug_form_package")


class PrescriptionStatus(str, Enum):
    Pending = 'Pending'
    Dispensed = 'Dispensed'
    All = 'All'
    PatiallyDispensed = 'Partially Dispensed'


class Prescription(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_prescription"
    id = Column(Integer, primary_key=True, index=True)
    consultant_id = Column(Integer,
                           ForeignKey("consultant_specialist.id", ondelete='cascade'))  # Could link to a User table
    client_id = Column(Integer, ForeignKey("client.id", ondelete='cascade'))  # Could link to a Client table
    pharmacy_id = Column(Integer, ForeignKey("pharmacy.id", ondelete='cascade'))
    status = Column(SqlEnum(PrescriptionStatus), default=PrescriptionStatus.Pending)
    instruction = Column(Text)
    note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    details = relationship("PrescriptionDetail", backref="prescription", cascade="all, delete-orphan")
    client = relationship("Client")
    consultant = relationship("Specialist")


class PrescriptionDetail(Base, SoftDeleteMixin):
    __tablename__ = "pharmacy_prescription_detail"
    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("pharmacy_drug.id", ondelete="cascade"))
    prescription_id = Column(Integer, ForeignKey("pharmacy_prescription.id", ondelete="cascade"))
    form = Column(SqlEnum(Form))
    frequency = Column(String(20))
    weight_volume = Column(String(20))
    interval = Column(String(15))
    dosage = Column(String(25))
    duration = Column(String(20))
    status = Column(SqlEnum(PrescriptionStatus), default=PrescriptionStatus.Pending)
    is_prn = Column(Boolean, default=False)
