import polib

def compile_po_to_mo(po_path):
    po = polib.pofile(po_path)
    mo_path = po_path.replace(".po", ".mo")
    po.save_as_mofile(mo_path)
    print(f"Compiled: {mo_path}")

compile_po_to_mo("locales/es/LC_MESSAGES/messages.po")
compile_po_to_mo("locales/en/LC_MESSAGES/messages.po")