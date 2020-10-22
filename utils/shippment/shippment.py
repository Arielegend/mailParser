class Shippment:
    def __init__(self, name: str, openedAt: str, SHO: str,
                 shippmentType: str, PO: str, supplier: str,
                 portDestination: str, portLoading: str, terms: str):
        self.name = name
        self.openedAt = openedAt
        self.SHO = SHO
        self.shippmentType = shippmentType
        self.PO = PO
        self.supplier = supplier
        self.portDestination = portLoading
        self.terms = terms
