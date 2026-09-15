from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os

from utils.text_extractor import extract_text
from utils.similarity import calculate_similarity


app = Flask(__name__)

# Folder where uploaded files will be stored
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Allowed file types
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/check", methods=["POST"])
def check_similarity():

    # Check if both files were uploaded
    if "reference_file" not in request.files:
        return "Reference file is missing."

    if "submitted_file" not in request.files:
        return "Submitted file is missing."

    reference_file = request.files["reference_file"]
    submitted_file = request.files["submitted_file"]

    # Check if user actually selected files
    if reference_file.filename == "":
        return "Please select a reference file."

    if submitted_file.filename == "":
        return "Please select a submitted file."

    # Check file types
    if not allowed_file(reference_file.filename):
        return "Reference file must be PDF, DOCX, or TXT."

    if not allowed_file(submitted_file.filename):
        return "Submitted file must be PDF, DOCX, or TXT."

    # Make filenames safe
    reference_filename = secure_filename(reference_file.filename)
    submitted_filename = secure_filename(submitted_file.filename)

    # Create complete paths
    reference_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        reference_filename
    )

    submitted_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        submitted_filename
    )

    # Save files
    reference_file.save(reference_path)
    submitted_file.save(submitted_path)

    try:

        # Extract text from both documents
        reference_text = extract_text(reference_path)
        submitted_text = extract_text(submitted_path)

        # Make sure documents contain text
        if not reference_text.strip():
            return "Could not find text in the reference document."

        if not submitted_text.strip():
            return "Could not find text in the submitted document."

        # Calculate semantic similarity
        similarity = calculate_similarity(
            reference_text,
            submitted_text
        )

        # Determine similarity level
        if similarity >= 80:
            level = "Very High Similarity"
            message = "The documents contain a very high level of semantic similarity."

        elif similarity >= 60:
            level = "High Similarity"
            message = "The documents contain a high level of semantic similarity."

        elif similarity >= 40:
            level = "Moderate Similarity"
            message = "The documents contain a moderate level of semantic similarity."

        else:
            level = "Low Similarity"
            message = "The documents contain relatively low semantic similarity."

        return render_template(
            "report.html",
            similarity=similarity,
            level=level,
            message=message
        )

    except Exception as e:

        print("ERROR:", e)

        return "Something went wrong while analyzing the documents."


if __name__ == "__main__":
    app.run(debug=True)