# run this once to generate test PDF — not part of the project
from reportlab.pdfgen import canvas

pdf = canvas.Canvas("test_inputs/german_words.pdf")
pdf.setFont("Helvetica", 14)

words = [
    "der Apfel",
    "das Fenster", 
    "die Straße",
    "kaufen",
    "schlafen",
    "groß",
    "klein",
    "der Tisch",
    "laufen",
    "die Küche"
]

y = 750
for word in words:
    pdf.drawString(100, y, word)
    y -= 30

pdf.save()
print("PDF created!")