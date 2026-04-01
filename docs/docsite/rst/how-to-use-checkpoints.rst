How to use checkpoints
======================

The goal of checkpoints is to allow you to save when certain tasks were executed, so that you can later use this
information to skip tasks that have already been executed during later runs of, for example, update and upgrade procedures.

This of course is especially useful when you need to re-run a long procedure which failed at some point.

At the end of the day, checkpoints are just files touched on the target system, with a chosen name.

.. note::
    During updates and upgrades, to keep consistency between runs of the same procedure,
    checkpoints should be created in the same directory,
    which is automatically set to point to the correct folder for the current procedure.

Now, let's look at some examples of how to use checkpoints in your playbooks.

Example 1: Using checkpoints in a playbook
-------------------------------------------

In this example, we will create a checkpoint before executing a task and then check for that checkpoint before running the task again.

.. code-block:: yaml+jinja

    - name: Example playbook with checkpoints
      hosts: all

      tasks:
        - name: Retrieve checkpoints
          neteye.upgrade_manager.checkpoint:
            folder: "{{ checkpoints_folder }}"
          register: all_checkpoints

        - name: Perform some tasks if they were not executed before
          when: "'my_tasks' not in all_checkpoints.checkpoints"
          block:
            - name: Task 1
              ansible.builtin.debug:
                msg: "Executing Task 1"

            - name: Task 2
              ansible.builtin.debug:
                msg: "Executing Task 2"

            - name: Create checkpoint for my_tasks
              neteye.upgrade_manager.checkpoint:
                folder: "{{ checkpoints_folder }}"
                name: "my_tasks"
                state: present


Example 2: Set folder as module parameter to avoid repeating the variable
-------------------------------------------------------------------------

Most of the times the folder target of our checkpoints action does not change, so we can set it as default parameter
for our checkpoint module at the beginning of the playbook, to avoid repeating it every time we use the module.

Below you can find the same example as above, but with the folder set as a default parameter for the checkpoint module.

.. code-block:: yaml+jinja

    - name: Example playbook with checkpoints
      hosts: all
      module_defaults:
        neteye.upgrade_manager.checkpoint:
        folder: "{{ checkpoints_folder }}"

      tasks:
        - name: Retrieve checkpoints
          neteye.upgrade_manager.checkpoint:
          register: all_checkpoints

        - name: Perform some tasks if they were not executed before
          when: "'my_tasks' not in all_checkpoints.checkpoints"
          block:
            - name: Task 1
              ansible.builtin.debug:
                msg: "Executing Task 1"

            - name: Task 2
              ansible.builtin.debug:
                msg: "Executing Task 2"

            - name: Create checkpoint for my_tasks
              neteye.upgrade_manager.checkpoint:
                name: "my_tasks"
                state: present
