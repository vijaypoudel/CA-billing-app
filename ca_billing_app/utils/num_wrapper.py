def num_to_words(num, currency="INR"):
    """
    Converts a number to words based on the currency.
    """
    try:
        num = float(num)
        if num == 0:
            return "Zero"
            
        units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
        teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
        tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
        
        def convert_chunk(n):
            if n < 10:
                return units[n]
            elif n < 20:
                return teens[n-10]
            elif n < 100:
                return tens[n//10] + (" " + units[n%10] if n%10 != 0 else "")
            elif n < 1000:
                return units[n//100] + " Hundred" + (" and " + convert_chunk(n%100) if n%100 != 0 else "")
            return ""

        integer_part = int(num)
        decimal_part = int(round((num - integer_part) * 100))
        
        words = []
        
        if currency == "INR":
            # Indian Number System: Crore, Lakh, Thousand, Hundred
            crore = integer_part // 10000000
            integer_part %= 10000000
            lakh = integer_part // 100000
            integer_part %= 100000
            thousand = integer_part // 1000
            integer_part %= 1000
            hundred = integer_part // 100
            remainder = integer_part % 100
            
            if crore > 0: words.append(convert_chunk(crore) + " Crore")
            if lakh > 0: words.append(convert_chunk(lakh) + " Lakh")
            if thousand > 0: words.append(convert_chunk(thousand) + " Thousand")
            if hundred > 0: words.append(convert_chunk(hundred) + " Hundred")
            if remainder > 0:
                if words: words.append("and")
                words.append(convert_chunk(remainder))
                
            main_curr = "Rupees"
            sub_curr = "Paise"
        else:
            # International Number System: Billion, Million, Thousand
            billion = integer_part // 1000000000
            integer_part %= 1000000000
            million = integer_part // 1000000
            integer_part %= 1000000
            thousand = integer_part // 1000
            remainder = integer_part % 1000
            
            if billion > 0: words.append(convert_chunk(billion) + " Billion")
            if million > 0: words.append(convert_chunk(million) + " Million")
            if thousand > 0: words.append(convert_chunk(thousand) + " Thousand")
            if remainder > 0:
                words.append(convert_chunk(remainder))
                
            if currency == "USD":
                main_curr, sub_curr = "Dollars", "Cents"
            elif currency == "EUR":
                main_curr, sub_curr = "Euros", "Cents"
            elif currency == "GBP":
                main_curr, sub_curr = "Pounds", "Pence"
            else:
                main_curr, sub_curr = currency, "Cents"

        result = " ".join(words) + f" {main_curr}"
        
        if decimal_part > 0:
            result += f" and {convert_chunk(decimal_part)} {sub_curr}"
            
        result += " Only"
        
        return result.title().replace("  ", " ").strip()
    except Exception:
        return str(num)
