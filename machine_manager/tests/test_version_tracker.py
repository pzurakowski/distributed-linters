import pytest
from math import ceil

from version_tracker import VersionTracker, Readjustment, UpdateStatus


def do_readjustment(tracker, readjustment):
    if readjustment is None:
        return

    for _ in range(readjustment.count):
        tracker.remove(readjustment.from_version)
        tracker.add(readjustment.to_version)


class TestConstructor:
    def test_empty_update_steps_list(self):
        with pytest.raises(ValueError):
            VersionTracker(initial_version="v1", update_steps=[])

    def test_update_steps_without_100(self):
        with pytest.raises(ValueError):
            VersionTracker(initial_version="v1", update_steps=[50, 90])


class TestDetermineVersion:
    def test_determine_version_without_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        assert tracker.determine_version() == "v1"

    def test_determine_version_prioritise_new_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)

        second_version = tracker.determine_version()
        assert second_version == "v1"
        tracker.add(second_version)

        third_version = tracker.determine_version()
        assert third_version == "v2"
        tracker.add(third_version)

    def test_determine_version_at_least_one_current(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[99, 100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)

        second_version = tracker.determine_version()
        assert second_version == "v1"
        tracker.add(second_version)

    def test_determine_version_at_full_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)

        second_version = tracker.determine_version()
        assert second_version == "v2"
        tracker.add(second_version)


class TestAdd:
    def test_add_with_invalid_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        with pytest.raises(ValueError):
            tracker.add("v2")

    def test_add_against_determine_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        readjustment = tracker.add("v1")

        assert readjustment is not None

    def test_add_remove_no_readjustment(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])

        version = tracker.determine_version()
        assert version == "v1"
        assert tracker.add(version) is None

        assert tracker.remove(version) is None


class TestRemove:
    def test_remove_with_zero_current_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        with pytest.raises(ValueError):
            tracker.remove("v1")

    def test_remove_with_zero_next_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")
        with pytest.raises(ValueError):
            tracker.remove("v2")

    def test_remove_with_invalid_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])

        first_version = tracker.determine_version()
        assert first_version == "v1"
        tracker.add(first_version)

        with pytest.raises(ValueError):
            tracker.remove("v2")

    def test_remove_the_only_next_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])

        first_version = tracker.determine_version()
        assert first_version == "v1"
        tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)
        do_readjustment(tracker, readjustment)

        second_version = tracker.determine_version()
        assert second_version == "v1"
        tracker.add(second_version)

        readjustment = tracker.remove("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)

    def test_remove_the_only_current_version(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)

        second_version = tracker.determine_version()
        assert second_version == "v1"
        tracker.add(second_version)

        readjustment = tracker.remove("v1")
        assert readjustment is None


class TestStartUpdate:
    def test_double_start_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")
        with pytest.raises(ValueError):
            tracker.start_update("v3")

    def test_start_update_with_zero_count(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        assert tracker.start_update("v2") is None

    def test_start_update_readjustment_small(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[10, 100])

        first_version = tracker.determine_version()
        assert first_version == "v1"
        tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)

    def test_start_update_readjustment_big(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])

        for _ in range(10):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=5)

    # QUESTION: Do we need fractional update steps?
    # The code should handle them, but is it a good idea to use them?
    def test_start_update_floats(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[0.1, 100])

        for _ in range(1000):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)

    def test_multiple_start_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])

        for _ in range(2):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)
        do_readjustment(tracker, readjustment)

        readjustment = tracker.move_to_next_step()
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)
        do_readjustment(tracker, readjustment)
        tracker.finish_update()

        readjustment = tracker.start_update("v3")
        assert readjustment == Readjustment(from_version="v2", to_version="v3", count=1)
        do_readjustment(tracker, readjustment)

        readjustment = tracker.move_to_next_step()
        assert readjustment == Readjustment(from_version="v2", to_version="v3", count=1)
        tracker.finish_update()


class TestMoveToNextStep:
    def test_move_to_next_step_without_start_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[10, 50, 100])
        with pytest.raises(ValueError):
            tracker.move_to_next_step()

    def test_move_to_next_step_on_last_step(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)

        with pytest.raises(ValueError):
            tracker.move_to_next_step()

    def test_move_to_next_step_no_readjustment(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[10, 50, 100])

        first_version = tracker.determine_version()
        assert first_version == "v1"
        tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)
        do_readjustment(tracker, readjustment)

        readjustment = tracker.move_to_next_step()
        assert readjustment is None

    def test_move_to_next_step_readjustment(self):
        tracker = VersionTracker(
            initial_version="v1", update_steps=[0.1, 1, 10, 50, 100]
        )

        for _ in range(2):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)

        for _ in [1, 10, 50]:
            readjustment = tracker.move_to_next_step()
            assert readjustment == Readjustment(
                from_version="v1", to_version="v2", count=1
            )

        readjustment = tracker.move_to_next_step()
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=2)

    def test_move_to_next_step_readjustment_fractions(self):
        tracker = VersionTracker(
            initial_version="v1", update_steps=[0.1, 1, 10, 50, 100]
        )

        for _ in range(11):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)

        for step in [1, 10, 50, 100]:
            readjustment = tracker.move_to_next_step()
            assert readjustment == Readjustment(
                from_version="v1", to_version="v2", count=ceil(11 * step / 100.0)
            )


class TestMoveToPreviousStep:
    def test_move_to_previous_step_without_start_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        with pytest.raises(ValueError):
            tracker.move_to_previous_step()

    def test_move_to_previous_step_on_first_step(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")
        tracker.move_to_previous_step()

        assert tracker.update_status().is_updating == False

    def test_move_to_previous_step_no_readjustment(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[10, 50, 100])

        first_version = tracker.determine_version()
        assert first_version == "v1"
        tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        assert readjustment == Readjustment(from_version="v1", to_version="v2", count=1)
        do_readjustment(tracker, readjustment)

        tracker.move_to_next_step()

        readjustment = tracker.move_to_previous_step()
        assert readjustment is None

    def test_move_to_previous_step_readjustment_fractions(self):
        tracker = VersionTracker(
            initial_version="v1", update_steps=[0.1, 1, 10, 50, 100]
        )

        for _ in range(11):
            first_version = tracker.determine_version()
            assert first_version == "v1"
            tracker.add(first_version)

        readjustment = tracker.start_update("v2")
        do_readjustment(tracker, readjustment)

        for _ in [1, 10, 50, 100]:
            readjustment = tracker.move_to_next_step()
            do_readjustment(tracker, readjustment)

        # There should be 11 v2s at the moment

        for step in [50, 10, 1, 0.1]:
            readjustment = tracker.move_to_previous_step()

            assert readjustment == Readjustment(
                from_version="v2", to_version="v1", count=11 - ceil(11 * step / 100.0)
            )


class TestFinishUpdate:
    def test_finish_update_with_no_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        with pytest.raises(ValueError):
            tracker.finish_update()

    def test_finish_update_on_partial_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")
        with pytest.raises(ValueError):
            tracker.finish_update()

    def test_finish_update_on_full_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")

        first_version = tracker.determine_version()
        assert first_version == "v2"
        tracker.add(first_version)
        tracker.move_to_next_step()

        tracker.finish_update()
        assert tracker.update_status() == UpdateStatus(
            is_updating=False, current_version="v2", next_version=None, progress=0
        )


class TestUpdateStatus:
    def test_update_status_without_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        assert tracker.update_status() == UpdateStatus(
            is_updating=False, current_version="v1", next_version=None, progress=0
        )

    def test_update_status_with_update(self):
        tracker = VersionTracker(initial_version="v1", update_steps=[50, 100])
        tracker.start_update("v2")

        assert tracker.update_status() == UpdateStatus(
            is_updating=True, current_version="v1", next_version="v2", progress=50
        )
