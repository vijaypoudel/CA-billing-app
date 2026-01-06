def num_to_words(num):
    """
    Converts a number to Indian Rupees words.
    Simple implementation for typical invoice amounts.
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
            return ""

        # Split into integer and decimal
        integer_part = int(num)
        decimal_part = int(round((num - integer_part) * 100))
        
        words = []
        
        # Indian Number System: Crore, Lakh, Thousand, Hundred
        crore = integer_part // 10000000
        integer_part %= 10000000
        
        lakh = integer_part // 100000
        integer_part %= 100000
        
        thousand = integer_part // 1000
        integer_part %= 1000
        
        hundred = integer_part // 100
        remainder = integer_part % 100
        
        if crore > 0:
            words.append(convert_chunk(crore) + " Crore")
        if lakh > 0:
            words.append(convert_chunk(lakh) + " Lakh")
        if thousand > 0:
            words.append(convert_chunk(thousand) + " Thousand")
        if hundred > 0:
            words.append(convert_chunk(hundred) + " Hundred")
        if remainder > 0:
            if words: words.append("and")
            words.append(convert_chunk(remainder))
            
        result = " ".join(words) + " Rupees Only"
        
        # Add paise if any? Usually invoices round off or ignore for 'Only', 
        # but strict accounting might want it. The image says 'two thousand ... only', implying integer.
        # We will ignore paise for the words unless significant.
        
        return result.title()
    except Exception:
        return str(num)
