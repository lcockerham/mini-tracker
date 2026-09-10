const availabilitySelect = document.getElementById("format_availability");

function setFieldVisibility(fieldId, visible) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    field.hidden = !visible;
    for (const control of field.querySelectorAll("input, select, textarea")) {
        control.disabled = !visible;
    }
}

function updateFormatFields() {
    const availability = availabilitySelect?.value;
    const physicalAvailable = availability !== "digital_only";
    const digitalAvailable = availability !== "physical_only";

    setFieldVisibility("physical-ownership-field", physicalAvailable);
    setFieldVisibility("physical-location-field", physicalAvailable);
    setFieldVisibility("digital-ownership-field", digitalAvailable);
    setFieldVisibility("digital-source-field", digitalAvailable);
}

if (availabilitySelect) {
    availabilitySelect.addEventListener("change", updateFormatFields);
    updateFormatFields();
}
