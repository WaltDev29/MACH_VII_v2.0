# brain/tools/__init__.py

from .vision_detect import vision_detect
from .vision_analyze import vision_analyze
from .robot_action import robot_action
from .grasp_object import grasp_object

# 에이전트가 사용할 모든 도구 리스트 (평탄 구조)
ALL_TOOLS = [
    vision_detect,
    vision_analyze,
    robot_action,
    grasp_object
]
