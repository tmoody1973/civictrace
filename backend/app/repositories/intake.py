"""Intake bundle + case-manifest persistence (MOO-719).

The bundle document carries the human's selection from the moment of approval, so the
worker recreates the case from durable state only — never from request memory.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.schemas.corpus import CorpusManifest
from app.schemas.intake import BundleStatus, CandidateBundle, IntakeSelection

BUNDLES_COLLECTION = "intake_bundles"
MANIFESTS_COLLECTION = "case_manifests"


class IntakeStore(Protocol):
    def save_bundle(self, bundle: CandidateBundle) -> None: ...
    def get_bundle(self, bundle_id: str) -> CandidateBundle | None: ...
    def save_selection(self, bundle_id: str, selection: IntakeSelection) -> None: ...
    def get_selection(self, bundle_id: str) -> IntakeSelection | None: ...
    def set_status(
        self, bundle_id: str, status: BundleStatus, *, reason: str | None = None,
        case_id: str | None = None,
    ) -> None: ...
    def save_manifest(self, manifest: CorpusManifest) -> None: ...
    def get_manifest(self, corpus_id: str) -> CorpusManifest | None: ...
    def list_manifests(self) -> list[CorpusManifest]: ...


class InMemoryIntakeStore:
    """Test/local double with the same contract."""

    def __init__(self) -> None:
        self._bundles: dict[str, CandidateBundle] = {}
        self._selections: dict[str, IntakeSelection] = {}
        self._manifests: dict[str, CorpusManifest] = {}

    def save_bundle(self, bundle: CandidateBundle) -> None:
        self._bundles[bundle.bundle_id] = bundle

    def get_bundle(self, bundle_id: str) -> CandidateBundle | None:
        return self._bundles.get(bundle_id)

    def save_selection(self, bundle_id: str, selection: IntakeSelection) -> None:
        self._selections[bundle_id] = selection

    def get_selection(self, bundle_id: str) -> IntakeSelection | None:
        return self._selections.get(bundle_id)

    def set_status(
        self, bundle_id: str, status: BundleStatus, *, reason: str | None = None,
        case_id: str | None = None,
    ) -> None:
        bundle = self._bundles[bundle_id]
        self._bundles[bundle_id] = bundle.model_copy(
            update={
                "status": status,
                "failure_reason": reason,
                "case_id": case_id or bundle.case_id,
            }
        )

    def save_manifest(self, manifest: CorpusManifest) -> None:
        self._manifests[manifest.corpus_id] = manifest

    def get_manifest(self, corpus_id: str) -> CorpusManifest | None:
        return self._manifests.get(corpus_id)

    def list_manifests(self) -> list[CorpusManifest]:
        return list(self._manifests.values())


class FirestoreIntakeStore:
    def __init__(self, client: Any) -> None:
        self._bundles = client.collection(BUNDLES_COLLECTION)
        self._manifests = client.collection(MANIFESTS_COLLECTION)

    def save_bundle(self, bundle: CandidateBundle) -> None:
        self._bundles.document(bundle.bundle_id).set(
            {"bundle": bundle.model_dump(mode="json")}, merge=True
        )

    def get_bundle(self, bundle_id: str) -> CandidateBundle | None:
        snapshot = self._bundles.document(bundle_id).get()
        if not snapshot.exists:
            return None
        return CandidateBundle.model_validate(snapshot.to_dict()["bundle"])

    def save_selection(self, bundle_id: str, selection: IntakeSelection) -> None:
        self._bundles.document(bundle_id).set(
            {"selection": selection.model_dump(mode="json")}, merge=True
        )

    def get_selection(self, bundle_id: str) -> IntakeSelection | None:
        snapshot = self._bundles.document(bundle_id).get()
        data = snapshot.to_dict() if snapshot.exists else None
        if not data or "selection" not in data:
            return None
        return IntakeSelection.model_validate(data["selection"])

    def set_status(
        self, bundle_id: str, status: BundleStatus, *, reason: str | None = None,
        case_id: str | None = None,
    ) -> None:
        bundle = self.get_bundle(bundle_id)
        if bundle is None:
            return
        updated = bundle.model_copy(
            update={
                "status": status,
                "failure_reason": reason,
                "case_id": case_id or bundle.case_id,
            }
        )
        self.save_bundle(updated)

    def save_manifest(self, manifest: CorpusManifest) -> None:
        self._manifests.document(manifest.corpus_id).set(
            {"manifest": manifest.model_dump(mode="json")}
        )

    def get_manifest(self, corpus_id: str) -> CorpusManifest | None:
        snapshot = self._manifests.document(corpus_id).get()
        if not snapshot.exists:
            return None
        return CorpusManifest.model_validate(snapshot.to_dict()["manifest"])

    def list_manifests(self) -> list[CorpusManifest]:
        return [
            CorpusManifest.model_validate(doc.to_dict()["manifest"])
            for doc in self._manifests.stream()
        ]
