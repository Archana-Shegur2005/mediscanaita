from flask import Flask, request, jsonify
import pytesseract
from pdf2image import convert_from_bytes
import re
import gc

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract_text():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        pdf_file = request.files["file"]
        images = convert_from_bytes(pdf_file.read(), fmt='jpeg')

        extracted_text = []
        for img in images:
            text = pytesseract.image_to_string(img, config="--psm 6")
            extracted_text.append(text)
            del img
            gc.collect()

        full_text = "\n".join(extracted_text)
        return jsonify(extract_parameters(full_text))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def extract_parameters(text: str) -> dict:
    patterns = {
        "Hemoglobin":  r"\bhemoglobin\b[^\d]{0,20}(\d{1,3}[.,]?\d*)",
        "WBC":         r"(?:wbc|total leucocyte count)[^\d]{0,20}(\d{3,6})",
        "Platelets":   r"\bplatelet[s]?\b[^\d]{0,20}(\d{1,3}[.,]?\d*)",
        "RBC":         r"\brbc\b[^\d]{0,20}(\d{1,2}[.,]?\d*)",
        "MCV":         r"\bmcv\b[^\d]{0,20}(\d{1,3}[.,]?\d*)",
        "ESR":         r"\besr\b[^\d]{0,20}(\d{1,3})",
        "Vitamin B12": r"vitamin\s?b[\s]?12[^\d]{0,20}(\d{2,5})",
    }

    joined = text.lower()
    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, joined, flags=re.I)
        if m:
            result[key] = m.group(1).replace(",", "")
    return result

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)