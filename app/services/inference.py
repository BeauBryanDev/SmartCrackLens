


def calculate_severity(mask_area_px: int, max_width_px: int) -> Severity:
    if mask_area_px > 5000 or max_width_px > 20:
        return Severity.HIGH
    elif mask_area_px > 1500 or max_width_px > 10:
        return Severity.MEDIUM
    else:
        return Severity.LOW
    
    