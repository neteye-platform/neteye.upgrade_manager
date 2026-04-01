#!/usr/bin/env python3

DOCUMENTATION = r"""
---
module: checkpoint

short_description: Creates and retrieves checkpoints on NetEye

version_added: "1.0.0"

description:
  - Creates or retrieves checkpoints on NetEye
  - It can be used to save the current state of the update/upgrade process to
    restore it later if it fails

options:
    name:
        description: Name of the checkpoint to create or delete.
                     When C(state) is V(absent), the name can be also a glob pattern or
                     a regex, controlled by the C(use_regex) parameter.
        required: false
        type: str
    folder:
        description: Folder in which to store the checkpoint
        required: true
        type: str
    state:
        description: Whether to create or delete the checkpoint.
        required: false
        type: str
        choices:
            present: Creates a checkpoint
            absent: Deletes a checkpoint. Available from C(NetEye 4.43)
    use_regex:
        description: If true, the name parameter is treated as a regex pattern. This parameter is considered only when
                     C(state) is V(absent).
        required: false
        type: bool
        default: false
        version_added: "NetEye 4.43"
"""

EXAMPLES = r"""
- name: Create a checkpoint
  neteye.upgrade_manager.checkpoint:
    name: my_checkpoint
    folder: /path/to/checkpoint/folder
    state: present
  register: checkpoint_creation_result

- name: Checking if a specific checkpoint exists
  neteye.upgrade_manager.checkpoint:
    name: my_checkpoint
    folder: /path/to/checkpoint/folder
  register: checkpoint_presence

- name: Retrieve all checkpoints
  neteye.upgrade_manager.checkpoint:
    folder: /path/to/checkpoint/folder
  register: all_checkpoints

- name: Delete a specific checkpoint
  neteye.upgrade_manager.checkpoint:
    folder: /path/to/checkpoint/folder
    name: my_checkpoint
    state: absent
  register: checkpoint_deletion_result

- name: Delete all checkpoints matching a glob
  neteye.upgrade_manager.checkpoint:
    folder: /path/to/checkpoint/folder
    name: "my*"
    state: absent
  register: checkpoint_deletion_result

- name: Delete all checkpoints matching a regex
  neteye.upgrade_manager.checkpoint:
    folder: /path/to/checkpoint/folder
    name: "my_checkpoint-[0-9]+"
    state: absent
    use_regex: true
  register: checkpoint_deletion_result
"""

RETURN = r"""
checkpoints:
    description:
      - List of checkpoints, if name is provided it will check only
      - for that checkpoint, otherwise it will return all checkpoints
      - When C(state) is V(absent), it will return the list of deleted checkpoints
    type: list
    elements: str
    returned: always
    sample: ["my_checkpoint"]
"""

from pathlib import Path

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.neteye.upgrade_manager.plugins.module_utils.checkpoints import (
    load_checkpoints,
    validate_checkpoint_path,
    delete_checkpoint,
)

import re

__metaclass__ = type

CHECKPOINT_SUBFOLDER = "checkpoints"


def run_module() -> None:
    module_args = dict(
        name=dict(type="str", required=False),
        folder=dict(type="str", required=True),
        state=dict(
            type=str,
            required=False,
            choices=["present", "absent"],
        ),
        use_regex=dict(type=bool, required=False, default=False),
        required_by={"state": "name"},
    )

    result = dict(
        changed=False,
        checkpoints=[],
    )

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    name = module.params["name"]
    folder = Path(module.params["folder"])
    state = module.params["state"]

    checkpoint_folder = folder / CHECKPOINT_SUBFOLDER

    # If a checkpoint name is provided, validate it as a valid path against the base directory
    if name:
        try:
            validate_checkpoint_path(checkpoint_folder, name)
        except ValueError as e:
            module.fail_json(msg=f"{e}", checkpoints=[], rc=1)

    if not state:
        result["changed"] = False

        result["checkpoints"] = load_checkpoints(checkpoint_folder, name)
    elif state == "present":
        checkpoint_file = checkpoint_folder / name

        # If we are in check mode we return the correct changed status based on the presence of the file
        if module.check_mode:
            result["changed"] = not checkpoint_file.exists()
            result["checkpoints"] = [name]
            module.exit_json(**result)

        checkpoint_folder.mkdir(parents=True, exist_ok=True)
        result["changed"] = not checkpoint_file.exists()
        checkpoint_file.touch()

        result["checkpoints"] = [name]
    else:
        # We want to delete one or more checkpoints
        # Three options:
        #   - name not defined: delete all checkpoints
        #   - name defined and use_regex is False: delete files treating name as a glob
        #   - name defined and use_regex is True: delete files but threat the name as a full Python regex

        checkpoints_to_delete = []

        # If name is defined, we need to check if it is a regex or a glob
        if name:
            if module.params["use_regex"]:
                # If it is a regex we compile it
                pattern = re.compile(name)
                # and we retrieve all checkpoints that match the regex
                checkpoints_to_delete = [
                    checkpoint.name
                    for checkpoint in checkpoint_folder.iterdir()
                    if pattern.match(checkpoint.name)
                ]
            else:
                # If it is a glob we retrieve all checkpoints that match the glob
                checkpoints_to_delete = [
                    checkpoint.name for checkpoint in checkpoint_folder.glob(name)
                ]
        else:
            # If name is not defined we retrieve all checkpoints
            checkpoints_to_delete = load_checkpoints(checkpoint_folder)

        # Already set the list of checkpoints to delete and the changed status
        result["changed"] = len(checkpoints_to_delete) > 0
        result["checkpoints"] = [checkpoint for checkpoint in checkpoints_to_delete]

        # If we are in check mode we return the list of checkpoints to delete
        # and the correct changed status, without deleting anything
        if module.check_mode:
            module.exit_json(**result)

        # If we are not in check mode we delete all retrieved checkpoints, validating first the path
        for checkpoint in checkpoints_to_delete:
            try:
                validate_checkpoint_path(checkpoint_folder, checkpoint)
            except ValueError as e:
                module.fail_json(msg=f"{e}", checkpoints=[], rc=1)
            delete_checkpoint(checkpoint_folder, checkpoint)

    module.exit_json(**result)


def main() -> None:
    run_module()


if __name__ == "__main__":
    main()
