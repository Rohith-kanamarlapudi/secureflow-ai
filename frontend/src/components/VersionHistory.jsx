import { useEffect, useState } from "react";

export default function VersionHistory({ documentId, token }) {
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [signatureStatus, setSignatureStatus] = useState({});

    useEffect(() => {
        if (!documentId) {
            return;
        }

        loadVersions();
    }, [documentId]);

    async function loadVersions() {
        try {
            setLoading(true);
            setError("");

            const response = await fetch(
                `http://localhost:8000/documents/${documentId}/versions`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Failed to load versions (${response.status})`
                );
            }

            const data = await response.json();

            setVersions(data);

            // Load signature status for every version
            for (const version of data) {
                loadSignatureStatus(version.id);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }

    async function loadSignatureStatus(versionId) {
        try {
            const response = await fetch(
                `http://localhost:8000/documents/${documentId}/versions/${versionId}/signature`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            setSignatureStatus((previous) => ({
                ...previous,
                [versionId]: data,
            }));
        } catch (err) {
            console.error(
                "Failed to load signature status:",
                err
            );
        }
    }

    async function downloadVersion(versionId) {
        try {
            const response = await fetch(
                `http://localhost:8000/documents/${documentId}/versions/${versionId}/download`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error(
                    `Download failed (${response.status})`
                );
            }

            const blob = await response.blob();

            const url = window.URL.createObjectURL(blob);

            const link = document.createElement("a");
            link.href = url;
            link.download = "document-version";
            document.body.appendChild(link);
            link.click();

            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            alert(err.message);
        }
    }

    if (loading) {
        return (
            <div className="p-4">
                Loading version history...
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 text-red-600">
                {error}
            </div>
        );
    }

    return (
        <div className="mt-6 rounded-lg border p-4">
            <h2 className="mb-4 text-xl font-semibold">
                Version History
            </h2>

            {versions.length === 0 ? (
                <p className="text-gray-500">
                    No versions found.
                </p>
            ) : (
                <div>
                    {versions.map((version) => {
                        const sig =
                            signatureStatus[version.id];

                        const isValid =
                            sig?.status === "VALID";

                        return (
                            <div
                                key={version.id}
                                className="flex items-center justify-between border-b py-3"
                            >
                                <div>
                                    <div className="font-medium">
                                        Version{" "}
                                        {version.version}
                                    </div>

                                    <div className="text-sm text-gray-500">
                                        SHA-256:{" "}
                                        {version.sha256_hash}
                                    </div>

                                    {sig && (
                                        <div
                                            className={
                                                isValid
                                                    ? "text-green-600"
                                                    : "text-red-600"
                                            }
                                        >
                                            {sig.status}{" "}
                                            {sig.signer
                                                ? `• ${sig.signer}`
                                                : ""}{" "}
                                            •{" "}
                                            {sig.modified
                                                ? "Modified"
                                                : "Unmodified"}
                                        </div>
                                    )}
                                </div>

                                <button
                                    onClick={() =>
                                        downloadVersion(
                                            version.id
                                        )
                                    }
                                    className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
                                >
                                    Download
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}