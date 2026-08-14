import { useState } from "react";

import { api } from "../api/client";

export default function UploadForm({ onUploadSuccess }) {
    const [selectedFile, setSelectedFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleFileChange = (event) => {
        const file = event.target.files?.[0] || null;

        setSelectedFile(file);
        setError("");
        setSuccess("");
    };

    const handleUpload = async (event) => {
        event.preventDefault();

        setError("");
        setSuccess("");

        if (!selectedFile) {
            setError("Please select a file first.");
            return;
        }

        const formData = new FormData();

        // This name MUST match FastAPI:
        // file: UploadFile = File(...)
        formData.append("file", selectedFile);

        setUploading(true);

        try {
            const response = await api.post(
                "/documents",
                formData
            );

            console.log("Upload successful:", response.data);

            setSuccess(
                `Uploaded "${selectedFile.name}" successfully.`
            );

            setSelectedFile(null);

            // Reset the file input
            event.target.reset();

            // Refresh document list
            if (onUploadSuccess) {
                onUploadSuccess();
            }

        } catch (error) {
            console.error("Upload failed:", error);

            if (error.response?.status === 401) {
                setError(
                    "Authentication failed. Please login again."
                );

                localStorage.removeItem("access_token");
                localStorage.removeItem("refresh_token");

                return;
            }

            if (error.response?.data?.detail) {
                const detail = error.response.data.detail;

                setError(
                    typeof detail === "string"
                        ? detail
                        : JSON.stringify(detail)
                );

                return;
            }

            setError(
                "Failed to upload document. Please check the backend."
            );

        } finally {
            setUploading(false);
        }
    };

    return (
        <section className="upload-section">

            <h3>Upload Document</h3>

            <p>
                Select a document to upload securely.
            </p>

            <form onSubmit={handleUpload}>

                <div className="upload-controls">

                    <input
                        type="file"
                        onChange={handleFileChange}
                        disabled={uploading}
                    />

                    <button
                        type="submit"
                        disabled={uploading || !selectedFile}
                        className="upload-btn"
                    >
                        {uploading ? "Uploading..." : "Upload"}
                    </button>

                </div>

            </form>

            {error && (
                <div className="error-message">
                    {error}
                </div>
            )}

            {success && (
                <div className="success-message">
                    {success}
                </div>
            )}

        </section>
    );
}