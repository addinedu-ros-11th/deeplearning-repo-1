import numpy as np
import sys
import os

# ensure src/ is on path so package imports work when running tests from repo root
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from detectors.product_dl import ProductRecognizer


class FakeTensor:
    def __init__(self, arr):
        self._arr = np.array(arr)

    def cpu(self):
        return self

    def numpy(self):
        return self._arr


class FakeBox:
    def __init__(self, xyxy, cls, conf):
        self.xyxy = [FakeTensor(xyxy)]
        self.cls = [cls]
        self.conf = [conf]


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes


class DummyModel:
    def __init__(self, results_sequence):
        # results_sequence is a list of lists of FakeBox objects for each call
        self._seq = results_sequence
        self._idx = 0

    def predict(self, frame, conf=None, verbose=False):
        # Return a list-like where index 0 has .boxes attribute
        if self._idx >= len(self._seq):
            # return empty result
            self._idx += 1
            return [FakeResult([])]
        boxes = self._seq[self._idx]
        self._idx += 1
        return [FakeResult(boxes)]


def test_recognize_with_trigger_added_after_duration():
    pr = ProductRecognizer(model_path=None)
    pr.required_duration = 1.0  # make test faster
    # patch model
    # Prepare detections for 3 frames: detect, detect, detect (should be added after 2nd->3rd)
    boxes = [FakeBox([10, 10, 20, 20], cls=0, conf=0.95)]
    model = DummyModel([boxes, boxes, boxes])
    pr.model = model

    t0 = 1000.0
    r1 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0
    )
    assert r1["status"] in ("tracking", "none")

    r2 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0 + 0.6
    )
    assert r2["status"] == "tracking"
    assert r2["main_event"]["status"] == "tracking"

    r3 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0 + 1.1
    )
    assert r3["status"] == "added"
    assert r3["main_event"]["status"] == "added"


def test_cooldown_prevents_immediate_readd():
    pr = ProductRecognizer(model_path=None)
    pr.required_duration = 0.5
    pr.cooldown_seconds = 2.0

    boxes = [FakeBox([10, 10, 20, 20], cls=1, conf=0.9)]
    model = DummyModel([boxes, boxes, boxes, boxes])
    pr.model = model

    t0 = 2000.0
    # call a few times and ensure one of the calls returns 'added'
    r1 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0
    )
    r2 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0 + 0.6
    )
    r3 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=t0 + 0.7
    )

    statuses = {r1.get("status"), r2.get("status"), r3.get("status")}
    assert "added" in statuses

    # find which call added and then verify cooldown behavior on the next observation
    added_time = None
    for idx, r in enumerate((r1, r2, r3)):
        if r.get("status") == "added":
            added_time = [t0, t0 + 0.6, t0 + 0.7][idx]
            break

    assert added_time is not None

    # immediately show again within cooldown (0.5s after added)
    res2 = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=added_time + 0.5
    )
    # status should either be 'none' or report cooldown for that product
    assert res2["status"] in ("none", "tracking") or any(
        d.get("state") == "cooldown" for d in res2.get("all_detections", [])
    )


def test_no_detection_returns_none():
    pr = ProductRecognizer(model_path=None)
    pr.model = DummyModel([[]])

    res = pr.recognize_with_trigger(
        np.zeros((100, 100, 3), dtype=np.uint8), current_time=3000.0
    )
    assert res["status"] == "none"
