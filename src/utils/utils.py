def convert_to_float(number):
    try:
        result = float(number)
        if result > 0:
            return True
        return False
    except Exception as e:
        return False
