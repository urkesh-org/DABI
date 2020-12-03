

for i in range(0, 90):
    note = f'{str(i).zfill(2)}'
    text = f"""T 3. Notes
S Giorgio Buccellati
CH {i}
HTML notes

"""
    with open(note+'.md','w') as file:
        file.write(text)
    




