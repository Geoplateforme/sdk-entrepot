from typing import Any, Dict, List, Optional

from unittest.mock import PropertyMock, call, patch, MagicMock

from ignf_gpf_sdk.io.Config import Config
from ignf_gpf_sdk.store.ProcessingExecution import ProcessingExecution
from ignf_gpf_sdk.store.StoredData import StoredData
from ignf_gpf_sdk.store.Upload import Upload
from ignf_gpf_sdk.workflow.action.ActionAbstract import ActionAbstract
from ignf_gpf_sdk.workflow.action.ProcessingExecutionAction import ProcessingExecutionAction
from ignf_gpf_sdk.Errors import GpfSdkError
from tests.GpfTestCase import GpfTestCase


# pylint:disable=too-many-arguments
# pylint:disable=too-many-locals
# pylint:disable=too-many-branches
# pylint:disable=too-many-statements
# fmt: off
class ProcessingExecutionActionTestCase(GpfTestCase):
    """Tests ProcessingExecutionAction class.

    cmd : python3 -m unittest -b tests.workflow.action.ProcessingExecutionActionTestCase
    """

    def test_find_stored_data(self) -> None:
        """Test find_stored_data."""
        o_pe1 = ProcessingExecution({"_id": "pe_1"})
        o_pe2 = ProcessingExecution({"_id": "pe_2"})
        # création du dict décrivant l'action
        d_action:Dict[str, Any] = {
            "type": "processing-execution",
            "body_parameters": {
                "output": {
                    "stored_data": {"name": "name_stored_data"}
                }
            },
            "tags": {"tag": "val"}
        }
        # exécution de ProcessingExecutionAction
        o_ua = ProcessingExecutionAction("contexte", d_action)

        for s_datastore in [None, "datastore"]:
            ## execution sans datastore
            # Mock de ActionAbstract.get_filters et Upload.api_list
            with patch.object(ActionAbstract, "get_filters", return_value=({"info":"val"}, {"tag":"val"})) as o_mock_get_filters:
                with patch.object(StoredData, "api_list", return_value=[o_pe1, o_pe2]) as o_mock_api_list :
                    # Appel de la fonction find_upload
                    o_stored_data = o_ua.find_stored_data(s_datastore)
                    # Vérifications
                    o_mock_get_filters.assert_called_once_with("processing_execution", d_action["body_parameters"]["output"]["stored_data"], d_action["tags"])
                    o_mock_api_list.assert_called_once_with(infos_filter={"info":"val"}, tags_filter={"tag":"val"}, datastore=s_datastore)
                    self.assertEqual(o_stored_data, o_pe1)

    def run_args(self,
        tags: Optional[Dict[str,Any]],
        comments: Optional[List[str]],
        s_key: str,
        s_type_output: str,
        datastore: Optional[str],
        output_already_exist: bool = False,
        behavior: Optional[str] = None,
    ) -> None:
        """lancement + test de ProcessingExecutionAction.run selon param

        Args:
            tags (Optional[Dict[str, Any]]): dictionnaire des tags ou None
            comments (Optional[List]): liste des commentaires ou None
            s_type_output (str): type de l'output (stored_data ou upload)
        """
        d_action: Dict[str, Any] = {"type": "processing-execution", "body_parameters":{"output":{s_key:"test"}}}
        if tags is not None:
            d_action["tags"] = tags
        if comments is not None:
            d_action["comments"] = comments

        # initialisation de ProcessingExecutionAction
        o_pea = ProcessingExecutionAction("contexte", d_action, behavior=behavior)

        # mock de processing execution
        d_store_properties = {"output": {s_type_output: {"_id": "id"}}}
        o_mock_precession = MagicMock()
        o_mock_precession.get_store_properties.return_value = d_store_properties
        o_mock_precession.api_launch.return_value = None

        # mock de upload
        o_mock_upload = MagicMock()
        o_mock_upload.api_add_tags.return_value = None
        o_mock_upload.api_add_comment.return_value = None

        # mock de stored_data
        o_mock_stored_data = MagicMock()
        o_mock_stored_data.api_add_tags.return_value = None
        o_mock_stored_data.api_add_comment.return_value = None

        # résultat de ProcessingExecutionAction."find_stored_data"
        o_exist_output = None
        if output_already_exist:
            o_mock_exist_output = MagicMock()
            o_mock_exist_output.api_delete.return_value = None
            o_exist_output = o_mock_exist_output

        # suppression de la mise en page forcée pour le with
        with patch.object(Upload, "api_get", return_value=o_mock_upload) as o_mock_processing_upload_api_get, \
            patch.object(StoredData, "api_get", return_value=o_mock_stored_data) as o_mock_processing_store_data_api_get, \
            patch.object(ProcessingExecution, "api_create", return_value=o_mock_precession) as o_mock_processing_execution_api_create, \
            patch.object(ProcessingExecutionAction, "find_stored_data", return_value=o_exist_output) as o_mock_find_stored_data, \
            patch.object(ProcessingExecutionAction, "output_new_entity", new_callable=PropertyMock, return_value=output_already_exist), \
            patch.object(Config, "get_str", return_value="STOP") \
        :
            # dans le cas où une entité existe déjà dans la gpf :
            if output_already_exist:
                if not behavior or behavior == "STOP":
                    # on attend une erreur
                    with self.assertRaises(GpfSdkError) as o_err:
                        o_pea.run(datastore)
                    self.assertEqual(o_err.exception.message, f"Impossible de créer l’exécution de traitement, une donnée stockée en sortie équivalente {o_exist_output} existe déjà.")
                    return

                if behavior == "DELETE":
                    # suppression de l'existant puis normal
                    ### @Ludivine, ça veut dire quoi ??
                    o_pea.run(datastore)
                    # un appel à find_stored_data
                    o_mock_find_stored_data.assert_called_once_with(datastore)
                    o_mock_exist_output.api_delete.assert_called_once_with()
                elif behavior == "CONTINUE":
                    return
                else:
                    # behavior non reconnu. On attend une erreur
                    with self.assertRaises(GpfSdkError) as o_err:
                        o_pea.run(datastore)
                    self.assertEqual(o_err.exception.message, f"Le comportement {behavior} n'est pas reconnu (STOP|DELETE|CONTINUE), l'exécution de traitement n'est pas possible.")
                    return

            else:
                if behavior == "CONTINUE":
                    return
                else:
                    # on lance l'exécution de run
                    ### @Ludivine, c'est à dire ?
                    o_pea.run(datastore)
                    o_mock_find_stored_data.assert_not_called()

            # test de l'appel à ProcessingExecution.api_create
            o_mock_processing_execution_api_create.assert_called_once_with({**d_action['body_parameters'], "datastore":datastore})
            # un appel à ProcessingExecution().get_store_properties
            o_mock_precession.get_store_properties.assert_called_once_with()

            # verif appel à Upload/StoredData
            if "stored_data" in d_store_properties["output"]:
                # test  .api_get
                o_mock_processing_store_data_api_get.assert_called_once_with("id", datastore=datastore)
                o_mock_processing_upload_api_get.assert_not_called()

                # test api_add_tags
                if "tags" in d_action and d_action["tags"]:
                    o_mock_stored_data.api_add_tags.assert_called_once_with(d_action["tags"])
                else:
                    o_mock_stored_data.api_add_tags.assert_not_called()
                o_mock_upload.api_add_tags.assert_not_called()

                # test commentaires
                if "comments" in d_action and d_action["comments"]:
                    self.assertEqual(len(d_action["comments"]), o_mock_stored_data.api_add_comment.call_count)
                    for s_comm in d_action["comments"]:
                        o_mock_stored_data.api_add_comment.assert_any_call({"text": s_comm})
                else:
                    o_mock_stored_data.api_add_comment.assert_not_called()
                o_mock_upload.api_add_comment.assert_not_called()


            elif "upload" in  d_store_properties["output"]:
                # test  .api_get
                o_mock_processing_upload_api_get.assert_called_once_with("id", datastore=datastore)
                o_mock_processing_store_data_api_get.assert_not_called()

                # test api_add_tags
                if "tags" in d_action and d_action["tags"]:
                    o_mock_upload.api_add_tags.assert_called_once_with(d_action["tags"])
                else:
                    o_mock_upload.api_add_tags.assert_not_called()
                o_mock_stored_data.api_add_tags.assert_not_called()

                # test commentaires
                if "comments" in d_action and d_action["comments"]:
                    self.assertEqual(len(d_action["comments"]), o_mock_upload.api_add_comment.call_count)
                    for s_comm in d_action["comments"]:
                        o_mock_upload.api_add_comment.assert_any_call({"text": s_comm})
                else:
                    o_mock_upload.api_add_comment.assert_not_called()
                o_mock_stored_data.api_add_comment.assert_not_called()

            # un appel à api_launch
            o_mock_precession.api_launch.assert_called_once_with()

    def test_run(self) -> None:
        """test de run"""
        # test upload
        for s_datastore in [None, "datastore"]:
            for s_type_output in [ "upload", "stored_data"]:
                s_key = "name"
                ## sans tag + sans commentaire
                self.run_args(None, None, s_key, s_type_output, s_datastore)
                ## tag vide + commentaire vide
                self.run_args({}, [], s_key, s_type_output, s_datastore)
                ## 1 tag + 1 commentaire
                self.run_args({"tag1": "val1"}, ["comm1"], s_key, s_type_output, s_datastore)
                ## 2 tag + 4 commentaire
                self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore)

        # tests particuliers pour cas ou la sortie existe déjà
        self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore, True, "STOP")
        self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore, True, "DELETE")
        self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore, True, "CONTINUE")
        self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore, True, "Toto")
        self.run_args({"tag1": "val1", "tag2": "val2"}, ["comm1", "comm2", "comm3", "comm4"], s_key, s_type_output, s_datastore, True, None)

    def monitoring_until_end_args(self, s_status_end: str, b_waits: bool, b_callback: bool) -> None:
        """lancement + test de ProcessingExecutionAction.monitoring_until_end() selon param

        Args:
            s_status_end (str): status de fin
            b_waits (bool): si on a des status intermédiaire
            b_callback (bool): si on a une fonction callback
        """

        if b_waits:
            l_status = [ProcessingExecution.STATUS_CREATED,ProcessingExecution.STATUS_WAITING, ProcessingExecution.STATUS_PROGRESS]
        else:
            l_status = []
        if b_callback:
            f_callback = MagicMock()
        else:
            f_callback = None

        # mock de o_mock_processing_execution
        o_mock_processing_execution = MagicMock(name="test")
        o_mock_processing_execution.get_store_properties.side_effect = [{"status": el} for el in l_status] + [{"status": s_status_end}]*3
        o_mock_processing_execution.api_update.return_value = None

        with patch.object(ProcessingExecutionAction, "processing_execution", new_callable=PropertyMock) as o_mock_pe, \
            patch.object(Config, "get_int", return_value=0) :
            o_mock_pe.return_value = o_mock_processing_execution

            # initialisation de ProcessingExecutionAction
            o_pea = ProcessingExecutionAction("contexte", {})
            s_return = o_pea.monitoring_until_end(f_callback)

            # vérification valeur de sortie
            self.assertEqual(s_return, s_status_end)

            # vérification de l'attente
            ## update
            self.assertEqual(o_mock_processing_execution.api_update.call_count, len(l_status))
            ##log + callback
            if f_callback is not None:
                self.assertEqual(f_callback.call_count, len(l_status)+1)
                self.assertEqual(f_callback.mock_calls, [call(o_mock_processing_execution)] * (len(l_status)+1))

    def interrupt_monitoring_until_end_args(self, s_status_end: str, b_waits: bool, b_callback: bool, b_upload: bool, b_stored_data: bool, b_new_output: bool) -> None:
        # cas interruption par l'utilisateur.
        """lancement + test de ProcessingExecutionAction.monitoring_until_end() + simulation ctrl+C pendant monitoring_until_end

        Args:
            s_status_end (str): status de fin
            b_waits (bool): si on a des status intermédiaire
            b_callback (bool): si on a une fonction callback
            b_upload (bool): si sortie du traitement en upload
            b_stored_data (bool): si sortie du traitement en stored-data
            b_new_output (bool): si on a une nouvelle sortie (création) un ancienne (modification)

        """

        if b_waits:
            l_status = [{"status": ProcessingExecution.STATUS_CREATED}, {"status": ProcessingExecution.STATUS_WAITING}, {"status": ProcessingExecution.STATUS_PROGRESS}, \
                {"raise": "KeyboardInterrupt"}, {"status": ProcessingExecution.STATUS_PROGRESS}, {"status": s_status_end}]
        else:
            l_status = [{"raise": "KeyboardInterrupt"}, {"status": s_status_end}]
        if b_callback:
            f_callback = MagicMock()
        else:
            f_callback = None

        d_definition_dict: Dict[str, Any] = {"body_parameters":{"output":{}}}
        d_output = {"name": "new"} if b_new_output else {"_id": "ancien"}
        if b_upload :
            o_mock_upload = MagicMock()
            o_mock_upload.api_delete.return_value = None
            o_mock_stored_data = None
            d_definition_dict["body_parameters"]["output"]["upload"]=d_output
        elif b_stored_data:
            o_mock_upload = None
            o_mock_stored_data = MagicMock()
            o_mock_stored_data.api_delete.return_value = None
            d_definition_dict["body_parameters"]["output"]["stored_data"]=d_output
        else:
            o_mock_upload = None
            o_mock_stored_data = None

        i_iter = 0
        def status() -> Dict[str, Any]:
            """fonction pour mock de get_store_properties (=> status)

            Raises:
                KeyboardInterrupt: simulation du Ctrl+C

            Returns:
                Dict[str, Any]: dict contenant le status
            """
            nonlocal i_iter
            s_el = l_status[i_iter]
            i_iter+=1
            if "raise" in s_el:
                raise KeyboardInterrupt()
            return s_el

        # mock de o_mock_processing_execution
        o_mock_processing_execution = MagicMock(name="test")
        o_mock_processing_execution.get_store_properties.side_effect = status
        o_mock_processing_execution.api_update.return_value = None
        o_mock_processing_execution.api_abort.return_value = None


        with patch.object(ProcessingExecutionAction, "processing_execution", new_callable=PropertyMock) as o_mock_pe, \
            patch.object(ProcessingExecutionAction, "upload", new_callable=PropertyMock) as o_mock_u, \
            patch.object(ProcessingExecutionAction, "stored_data", new_callable=PropertyMock) as o_mock_sd, \
            patch.object(Config, "get_int", return_value=0) :

            o_mock_pe.return_value = o_mock_processing_execution
            o_mock_u.return_value = o_mock_upload
            o_mock_sd.return_value = o_mock_stored_data

            # initialisation de ProcessingExecutionAction
            o_pea = ProcessingExecutionAction("contexte", d_definition_dict)

            # vérification sortie en erreur de monitoring_until_end
            with self.assertRaises(KeyboardInterrupt):
                o_pea.monitoring_until_end(f_callback)

            # exécution de abort
            if not b_waits:
                o_mock_processing_execution.api_abort.assert_not_called()
            else:
                o_mock_processing_execution.api_abort.assert_called_once_with()

            # vérification de l'attente
            ## update
            self.assertEqual(o_mock_processing_execution.api_update.call_count, len(l_status)-1)
            ##log + callback
            if f_callback is not None:
                self.assertEqual(f_callback.call_count, len(l_status)-2)
                self.assertEqual(f_callback.mock_calls, [call(o_mock_processing_execution)] * (len(l_status)-2))

            # vérification suppression el de sortie si nouveau
            if b_waits and s_status_end == ProcessingExecution.STATUS_ABORTED:
                if b_upload and o_mock_upload:
                    if b_new_output:
                        o_mock_upload.api_delete.assert_called_once_with()
                    else:
                        o_mock_upload.api_delete.assert_not_called()
                elif b_stored_data and o_mock_stored_data:
                    if b_new_output:
                        o_mock_stored_data.api_delete.assert_called_once_with()
                    else:
                        o_mock_stored_data.api_delete.assert_not_called()

    def test_monitoring_until_end(self)-> None:
        """test de test_monitoring_until_end"""
        for s_status_end in [ProcessingExecution.STATUS_ABORTED, ProcessingExecution.STATUS_SUCCESS, ProcessingExecution.STATUS_FAILURE]:
            for b_waits in [False, True]:
                for b_callback in [False, True]:
                    self.monitoring_until_end_args(s_status_end, b_waits, b_callback)
                    for b_new_output in [False, True]:
                        self.interrupt_monitoring_until_end_args(s_status_end, b_waits, b_callback, True, False, b_new_output)
                        self.interrupt_monitoring_until_end_args(s_status_end, b_waits, b_callback, False, True, b_new_output)
                        self.interrupt_monitoring_until_end_args(s_status_end, b_waits, b_callback, False, False, b_new_output)

    def test_output_new_entity(self)-> None:
        """test de output_new_entity"""
        for s_output in ["upload", "stored_data"]:
            for b_new in [True, False]:
                d_output = {"name": "new"} if b_new else {"_id": "ancien"}
                d_definition_dict: Dict[str, Any] = {"body_parameters":{"output":{s_output:d_output}}}
                # initialisation de ProcessingExecutionAction
                o_pea = ProcessingExecutionAction("contexte", d_definition_dict)
                self.assertEqual(o_pea.output_new_entity, b_new)


    def test_str(self) -> None:
        """test de __str__"""
        d_definition = {"_id": "ancien"}
        # test sans processing execution
        o_action = ProcessingExecutionAction("nom", d_definition)
        self.assertEqual("ProcessingExecutionAction(workflow=nom)", str(o_action))
        # test avec processing execution
        with patch('ignf_gpf_sdk.workflow.action.ProcessingExecutionAction.ProcessingExecutionAction.processing_execution', new_callable=PropertyMock) as o_mock_processing_execution:
            o_mock_processing_execution.return_value = MagicMock(id='test uuid')
            self.assertEqual("ProcessingExecutionAction(workflow=nom, processing_execution=test uuid)", str(o_action))
