from app.models.account import Account, PbUser
from app.models.branch import Branch
from app.models.customer import Customer, CustomerRelationship, CustomerInformation
from app.models.customer_account import CustomerAccount, CustomerTransaction
from app.models.product import Product, CustomerProduct, ProductMatching
from app.models.schedule import Schedule
from app.models.notification import Notification
from app.models.consultation import ConsultationMemo, ConsultationReport
from app.models.ai_todo import AiTodo
from app.models.kpi import Kpi
from app.models.handover import Handover
from app.models.in_charge import InCharge
from app.models.churn_level import ChurnLevel
from app.models.ml_raw import MlBaserateRaw, MlGoldRaw, MlRealestateRaw
from app.models.trend import (
    EconomicIndicatorHistory,
    EconomicIndicatorContribution,
    TrendLlmReport,
)

