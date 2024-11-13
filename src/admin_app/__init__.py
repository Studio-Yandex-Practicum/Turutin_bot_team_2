from sqlalchemy.ext import associationproxy

associationproxy.ASSOCIATION_PROXY = (
    associationproxy.AssociationProxyExtensionType.ASSOCIATION_PROXY
)
