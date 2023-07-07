import yaml

with open("opsml/registry/cards/templates/audit_card.yaml", "r") as stream:
    try:
        dict_ = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


from opsml.registry.cards.audit import AuditSections


audit = AuditSections()

print(audit.business_understanding[0].question)
