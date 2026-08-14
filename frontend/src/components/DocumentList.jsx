import { useEffect, useState } from "react";

import { api } from "../api/client";

export default function DocumentList() {
    const [docs, setDocs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        const fetchDocuments = async () => {
            try {
                const response = await api.get("/documents");
                setDocs(response.data);
            } catch (err) {
                console.error(err);
                setError("Failed to load documents");
            } finally {
                setLoading(false);
            }
        };

        fetchDocuments();
    }, []);

    if (loading) {
        return <p>Loading documents...</p>;
    }

    if (error) {
        return <p>{error}</p>;
    }

    return (
        <div className="w-full">
            <h2 className="mb-4 text-xl font-semibold">
                Documents
            </h2>

            {docs.length === 0 ? (
                <p>No documents found.</p>
            ) : (
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b">
                            <th className="px-4 py-2 text-left">
                                Filename
                            </th>
                            <th className="px-4 py-2 text-left">
                                MIME Type
                            </th>
                            <th className="px-4 py-2 text-left">
                                Created At
                            </th>
                        </tr>
                    </thead>

                    <tbody>
                        {docs.map((doc) => (
                            <tr
                                key={doc.id}
                                className="border-b"
                            >
                                <td className="px-4 py-2">
                                    {doc.filename}
                                </td>

                                <td className="px-4 py-2">
                                    {doc.mime_type || "-"}
                                </td>

                                <td className="px-4 py-2">
                                    {doc.created_at
                                        ? new Date(
                                              doc.created_at
                                          ).toLocaleString()
                                        : "-"}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            )}
        </div>
    );
}