import enum
from pydantic import BaseModel

class Experiments(enum.IntEnum):
    Unknown = 0
    GetRoleSelector = 1
    LynxExperimentRolloutView = 2
    BotReport = 3
    ServerAppealCertification = 4
    UserVotePrivacy = 5
    DevPortal = 6

class ExpStatus(enum.IntEnum):
    TODO = 0
    IN_PROGRESS = 1
    DONE = 2
    FAIL = 3
    TESTING = 4

class ExperimentProps(BaseModel):
    description: str
    status: ExpStatus
    min_perm: int
    rollout_allowed: bool

exp_props = {
    "Unknown": ExperimentProps(description="A test experiment", status=ExpStatus.DONE, min_perm=0, rollout_allowed = True),
    "GetRoleSelector": ExperimentProps(description="GetRoleSelector did not work out, switched to native roles", status=ExpStatus.FAIL, min_perm=0, rollout_allowed = False),
    "LynxExperimentRolloutView": ExperimentProps(description="Lynx rollout view experiment", status=ExpStatus.DONE, min_perm=5, rollout_allowed = True),
    "BotReport": ExperimentProps(description="Bot report in site experiment", status=ExpStatus.DONE, min_perm=0, rollout_allowed = True),
    "ServerAppealCertification": ExperimentProps(description="Ability to use request type of Appeal or Certification in server appeal (it is currently unknown what rules are to be implemented)", status=ExpStatus.IN_PROGRESS, min_perm=0, rollout_allowed = False),
    "UserVotePrivacy": ExperimentProps(description="User vote privacy experiment (flags=1 in update_profile)", status=ExpStatus.DONE, min_perm=0, rollout_allowed = True),
    "DevPortal": ExperimentProps(description="Dev Portal access experiment (never roll out this)", status=ExpStatus.TODO, min_perm=0, rollout_allowed = False),
}