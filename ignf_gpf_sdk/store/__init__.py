"""Classes représentant les entités de l'Entrepôt."""

from ignf_gpf_sdk.store.Annexe import Annexe
from ignf_gpf_sdk.store.Check import Check
from ignf_gpf_sdk.store.CheckExecution import CheckExecution
from ignf_gpf_sdk.store.Configuration import Configuration
from ignf_gpf_sdk.store.Datastore import Datastore
from ignf_gpf_sdk.store.Endpoint import Endpoint
from ignf_gpf_sdk.store.Offering import Offering
from ignf_gpf_sdk.store.Processing import Processing
from ignf_gpf_sdk.store.ProcessingExecution import ProcessingExecution
from ignf_gpf_sdk.store.Static import Static
from ignf_gpf_sdk.store.StoredData import StoredData
from ignf_gpf_sdk.store.Tms import Tms
from ignf_gpf_sdk.store.Upload import Upload
from ignf_gpf_sdk.store.User import User

# lien entre le nom/type texte et la classe
TYPE__ENTITY = {
    Annexe.entity_name(): Annexe,
    Check.entity_name(): Check,
    CheckExecution.entity_name(): CheckExecution,
    Configuration.entity_name(): Configuration,
    Datastore.entity_name(): Datastore,
    Endpoint.entity_name(): Endpoint,
    Offering.entity_name(): Offering,
    Processing.entity_name(): Processing,
    ProcessingExecution.entity_name(): ProcessingExecution,
    Static.entity_name(): Static,
    StoredData.entity_name(): StoredData,
    Tms.entity_name(): Tms,
    Upload.entity_name(): Upload,
    User.entity_name(): User,
}
