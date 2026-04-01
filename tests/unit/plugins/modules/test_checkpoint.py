import inspect
import random
import unittest
from pathlib import Path

from ansible_collections.neteye.upgrade_manager.plugins.modules import checkpoint
from ansible_collections.neteye.upgrade_manager.tests.test_utils.mock_ansible import (
    AnsibleExitJson,
    AnsibleFailJson,
    patchAnsibleModule,
    set_module_args,
)

WORKING_DIR = Path("/tmp/test_neteye_upgrade_manager_collection")


def current_function_name() -> str:
    return inspect.stack()[1].function


class TestCheckpoint(unittest.TestCase):
    def setUp(self) -> None:
        self.patches = [
            patchAnsibleModule(),
        ]

        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_fail_when_required_args_missing(self) -> None:
        set_module_args({})
        with self.assertRaises(AnsibleFailJson):
            checkpoint.main()

    def test_return_no_checkpoints(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        set_module_args(
            {
                "folder": base_dir.as_posix(),
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        self.assertTrue(set(result.exception.args[0]["checkpoints"]) == set())

        self.assertFalse(base_dir.exists())

    def test_create_a_checkpoint_changed(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))
        checkpoint_name = f"test_checkpoint_{random.randint(0, 1000)}"

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name,
                "state": "present",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"]) == set([checkpoint_name])
        )

        checkpoint_file = base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name

        self.assertTrue(checkpoint_file.exists())

    def test_create_a_checkpoint_no_changed(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))
        checkpoint_name = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file = base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name
        checkpoint_file.parent.mkdir(parents=True)
        checkpoint_file.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name,
                "state": "present",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"]) == set([checkpoint_name])
        )

        self.assertTrue(checkpoint_file.exists())

    def test_return_checkpoints(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))
        checkpoint_name = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file = base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name
        checkpoint_file.parent.mkdir(parents=True)
        checkpoint_file.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name,
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        log = Path("/tmp/ansible.log")
        log.write_text(str(result.exception.args[0]))
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"]) == set([checkpoint_name])
        )

        self.assertTrue(checkpoint_file.exists())

    def test_return_no_checkpoints_specify_name(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))
        checkpoint_name = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file = base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name,
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        self.assertTrue(set(result.exception.args[0]["checkpoints"]) == set())

        self.assertFalse(checkpoint_file.exists())

    def test_return_some_checkpoints(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))
        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"])
            == set([checkpoint_name_1, checkpoint_name_2]),
        )

        self.assertTrue(checkpoint_file_1.exists())
        self.assertTrue(checkpoint_file_2.exists())

    def test_checkpoint_creation_check_mode(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        base_dir.mkdir(parents=True)

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name_1,
                "state": "present",
                "_ansible_check_mode": True,
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"]) == set([checkpoint_name_1])
        )
        self.assertFalse(checkpoint_file_1.exists())

    def test_return_error_if_outside_basepath(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "../test_checkpoint",
            },
        )

        with self.assertRaises(AnsibleFailJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["failed"])
        self.assertTrue("does not start with" in result.exception.args[0]["msg"])

    def test_delete_specific_checkpoint(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name_1,
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(result.exception.args[0]["checkpoints"] == [checkpoint_name_1])
        self.assertFalse(checkpoint_file_1.exists())
        self.assertTrue(checkpoint_file_2.exists())

    def test_delete_specific_checkpoints_glob(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_deleteOne"
        checkpoint_name_3 = f"test_checkpoint_deleteTwo"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_3 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_3
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()
        checkpoint_file_3.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "test_checkpoint_delete*",
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"])
            == set([checkpoint_name_2, checkpoint_name_3])
        )
        self.assertTrue(checkpoint_file_1.exists())
        self.assertFalse(checkpoint_file_2.exists())
        self.assertFalse(checkpoint_file_3.exists())

    def test_delete_specific_checkpoints_regex(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_delete1"
        checkpoint_name_3 = f"test_checkpoint_delete4799357"
        checkpoint_name_4 = f"test_checkpoint_always_here"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_3 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_3
        )
        checkpoint_file_4 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_4
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()
        checkpoint_file_3.touch()
        checkpoint_file_4.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "test_checkpoint_delete[0-9]+",
                "state": "absent",
                "use_regex": True,
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"])
            == set([checkpoint_name_2, checkpoint_name_3])
        )
        self.assertTrue(checkpoint_file_1.exists())
        self.assertFalse(checkpoint_file_2.exists())
        self.assertFalse(checkpoint_file_3.exists())
        self.assertTrue(checkpoint_file_4.exists())

    def test_delete_specific_checkpoints_regex_but_regex_option_disabled(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_delete1"
        checkpoint_name_3 = f"test_checkpoint_delete4799357"
        checkpoint_name_4 = f"test_checkpoint_always_here"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_3 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_3
        )
        checkpoint_file_4 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_4
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()
        checkpoint_file_3.touch()
        checkpoint_file_4.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "test_checkpoint_delete[0-9]+",
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])
        self.assertTrue(result.exception.args[0]["checkpoints"] == [])
        self.assertTrue(checkpoint_file_1.exists())
        self.assertTrue(checkpoint_file_2.exists())
        self.assertTrue(checkpoint_file_3.exists())
        self.assertTrue(checkpoint_file_4.exists())

    def test_delete_all_checkpoints_using_glob(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_delete1"
        checkpoint_name_3 = f"test_checkpoint_delete4799357"
        checkpoint_name_4 = f"test_checkpoint_always_here"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_3 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_3
        )
        checkpoint_file_4 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_4
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()
        checkpoint_file_3.touch()
        checkpoint_file_4.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "*",
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"])
            == set(
                [
                    checkpoint_name_1,
                    checkpoint_name_2,
                    checkpoint_name_3,
                    checkpoint_name_4,
                ]
            )
        )
        self.assertFalse(checkpoint_file_1.exists())
        self.assertFalse(checkpoint_file_2.exists())
        self.assertFalse(checkpoint_file_3.exists())
        self.assertFalse(checkpoint_file_4.exists())

    def test_delete_returns_changed_when_checkpoint_is_deleted(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name_1,
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])

    def test_delete_returns_not_changed_when_checkpoint_is_not_deleted(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": "checkpoint_not_existing",
                "state": "absent",
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertFalse(result.exception.args[0]["changed"])

    def test_delete_check_mode(self) -> None:
        base_dir = WORKING_DIR / current_function_name() / str(random.randint(0, 1000))

        checkpoint_name_1 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_name_2 = f"test_checkpoint_{random.randint(0, 1000)}"
        checkpoint_file_1 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_1
        )
        checkpoint_file_2 = (
            base_dir / checkpoint.CHECKPOINT_SUBFOLDER / checkpoint_name_2
        )
        checkpoint_file_1.parent.mkdir(parents=True)
        checkpoint_file_1.touch()
        checkpoint_file_2.touch()

        set_module_args(
            {
                "folder": base_dir.as_posix(),
                "name": checkpoint_name_1,
                "state": "absent",
                "_ansible_check_mode": True,
            },
        )

        with self.assertRaises(AnsibleExitJson) as result:
            checkpoint.main()

        self.assertTrue(result.exception.args[0]["changed"])
        self.assertTrue(
            set(result.exception.args[0]["checkpoints"]) == set([checkpoint_name_1])
        )
        self.assertTrue(checkpoint_file_1.exists())
        self.assertTrue(checkpoint_file_2.exists())
