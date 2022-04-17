import enum
from pydantic import BaseModel

class Experiments(enum.IntEnum):
    Unknown = 0
    GetRolesSelector = 1
    LynxExperimentRolloutView = 2
    BotReport = 3

class ExpStatus(enum.IntEnum):
    TODO = 0
    IN_PROGRESS = 1
    DONE = 2

class ExperimentProps(BaseModel):
    description: str
    status: ExpStatus
    min_perm: int

exp_props = {
    "Unknown": ExperimentProps(description="A test experiment", status=ExpStatus.DONE, min_perm=0),
    "GetRolesSelector": ExperimentProps(description="Role selector on site experiment", status=ExpStatus.TODO, min_perm=0),
    "LynxExperimentRolloutView": ExperimentProps(description="Lynx rollout view experiment", status=ExpStatus.IN_PROGRESS, min_perm=5),
    "BotReport": ExperimentProps(description="Bot report in site experiment", status=ExpStatus.IN_PROGRESS, min_perm=0),
}