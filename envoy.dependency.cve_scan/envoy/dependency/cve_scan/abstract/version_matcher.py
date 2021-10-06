
from functools import cached_property
from typing import Dict, Optional

from packaging import version

import abstracts

from envoy.base import utils

from . import typing
from .dependency import ADependency


class ACVEVersionMatcher(metaclass=abstracts.Abstraction):

    def __init__(self, cpe_match: "typing.CVENodeMatchDict") -> None:
        self._cpe_match = cpe_match

    def __call__(self, dependency: ADependency) -> bool:
        if not dependency.release_version:
            return True
        return not (
            (self.version_info["end_exc"] is not None
             and (
                 dependency.release_version
                 >= self.version_info["end_exc"]))
            or (self.version_info["end_inc"] is not None
                and (
                    dependency.release_version
                    > self.version_info["end_inc"]))
            or (self.version_info["start_exc"] is not None
                and (
                    dependency.release_version
                    <= self.version_info["start_exc"]))
            or (self.version_info["start_inc"] is not None
                and (
                    dependency.release_version
                    < self.version_info["start_inc"])))

    @cached_property
    def version_info(self) -> Dict[str, Optional[version.Version]]:
        return {
            f"{action}_{ending}": self._cpe_version(action, ending)
            for action in ["end", "start"]
            for ending in ["exc", "inc"]}

    def _cpe_version(
            self,
            action: str,
            ending: str) -> Optional[version.Version]:
        version_info = self._cpe_match.get(
            f"version{action.capitalize()}{ending.capitalize()}luding", None)
        return (
            version.Version(utils.typed(str, version_info))
            if version_info is not None
            else None)
