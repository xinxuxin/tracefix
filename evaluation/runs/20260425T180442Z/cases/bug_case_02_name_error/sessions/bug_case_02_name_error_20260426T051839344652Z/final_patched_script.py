def checkout_total(price, tax_rate):
    totla = price * (1 + tax_rate)
    print(f"{totla:.2f}")


checkout_total(10, 0.07)
