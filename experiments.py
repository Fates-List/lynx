import enum
from pydantic import BaseModel

class Experiments(enum.IntEnum):
    Unknown = 0
    TestExperiment = 1
    LynxExperimentRolloutView = 2
    BotReport = 3

class ExpStatus(enum.IntEnum):
    TODO = 0
    IN_PROGRESS = 1
    DONE = 2
    FAIL = 3

class ExperimentProps(BaseModel):
    description: str
    status: ExpStatus
    min_perm: int

exp_props = {
    "Unknown": ExperimentProps(description="A test experiment", status=ExpStatus.DONE, min_perm=0),
    "TestExperiment": ExperimentProps(description="Test experiment #2 as GetRoleSelector did not work out", status=ExpStatus.FAIL, min_perm=0),
    "LynxExperimentRolloutView": ExperimentProps(description="Lynx rollout view experiment", status=ExpStatus.IN_PROGRESS, min_perm=5),
    "BotReport": ExperimentProps(description="Bot report in site experiment", status=ExpStatus.IN_PROGRESS, min_perm=0),
}