# -*- coding: utf-8 -*-
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from Acquisition import aq_inner
from plone.memoize.instance import memoize
from lxml import etree
from mediawiki import wiki2html
import re
import logging
from zope.site.hooks import getSite
from zope.component import queryUtility
from plone.i18n.normalizer.interfaces import IIDNormalizer
from xml.etree.ElementTree import iterparse
from je.casti.interfaces.interfaces import ICatalogoServicoPrefsForm
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
#Libs python
from suds.client import Client
from lx.tools import toolsMessageFactory as _


class LxToolsView(BrowserView):
    """Lx Tools"""

    __call__ = ViewPageTemplateFile('templates/lxtools.pt')

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.errors = {}

    def settings(self):
        if 'form.action.reindexIndexObject' in self.request.form:
            tipo_conteudo = self.request.get('tipo.conteudo', None)
            index_conteudo = self.request.get('index.conteudo', None)
            if self.validateReindexIndex(tipo_conteudo, index_conteudo):
                return self.reindexIndexObject(tipo_conteudo, index_conteudo)
        if 'form.action.parseXML' in self.request.form:
            file_xml = self.request.get('fileXML', None)
            folder_conteudo = self.request.get('folderMediaWiki', None)
            export_version = self.request.get('exportVersionXML', None)
            if self.validateParseXML(file_xml, folder_conteudo, export_version):
                return self.parseXML(file_xml, folder_conteudo, export_version)
        if 'form.action.tipoServico' in self.request.form:
            tipo_servico = self.request.get('tipoServico', None)
            folder_catalogo = self.request.get('folderCatalogo', None)
            if self.validateTipoServico(tipo_servico, folder_catalogo):
                return self.createAtividade(tipo_servico, folder_catalogo)

    def validateReindexIndex(self, tipo_conteudo, index_conteudo):
        """Validação do Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        if tipo_conteudo == None:
            self.errors['tipo_conteudo'] = "O campo é obrigatório."
        if index_conteudo == None:
            self.errors['index_conteudo'] = "O campo é obrigatório."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True

    def reindexIndexObject(self, tipo_conteudo, index_conteudo):
        """Reindex.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        ctool = getToolByName(self, 'portal_catalog')
        objects = ctool(portal_type=tipo_conteudo, sort_on='id', sort_order='ascending')
        log = logging.getLogger('REINDEX:')
        for object in objects:
            obj = object.getObject()
            try:
                obj.reindexObject(idxs=index_conteudo)
                log.info(obj.absolute_url_path() + ' CATALOGADO')
            except:
                log.info(obj.absolute_url_path() + ' ERRO')
        msg = 'Procedimento executado.'
        utils.addPortalMessage(msg, type='info')

    @memoize
    def getTypes(self):
        """
        """
        putils = getToolByName(self, 'plone_utils')
        allTypes = putils.getUserFriendlyTypes()
        allTypes = allTypes
        return sorted(allTypes, key=str.lower)

    @memoize
    def getIndexes(self):
        """Retorna todos os indices do catalog.
        """
        ctool = getToolByName(self, 'portal_catalog')
        indexs = ctool.getIndexObjects()
        indexs = [i.getId() for i in indexs]
        return sorted(indexs, key=str.lower)

    @memoize
    def validateParseXML(self, file_xml, folder_conteudo, export_version):
        """Validação do Parse XML.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        if file_xml.filename == '':
            self.errors['file_xml'] = "O campo é obrigatório."
        if (folder_conteudo == '') or (folder_conteudo.strip() == ''):
            self.errors['folder_conteudo'] = "O campo é obrigatório."
        if (export_version == ''):
            self.errors['export_version'] = "O campo é obrigatório."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True

    @memoize
    def parseXML(self, file_xml, folder_conteudo, export_version):
        """Parse XML.
        https://github.com/zikzakmedia/python-mediawiki
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')

        NS = '{http://www.mediawiki.org/xml/export-' + export_version + '/}'

        conteudo = []

        with open(file_xml.name) as f:
            for event, elem in iterparse(f):
                if elem.tag == '{0}page'.format(NS):
                    title = elem.find("{0}title".format(NS))
                    contr = elem.find(".//{0}username".format(NS))
                    text = elem.find(".//{0}text".format(NS))
                    if (title is not None) and (contr is not None) and (text is not None):
                        text = unicode(text.text).encode('utf-8')
                        text = wiki2html(text, True)
                        conteudo.append(dict(title=title.text, contr=contr.text, text=text))
                    elem.clear()

        self.createDocument(conteudo, folder_conteudo)

        msg = 'Procedimento executado.'
        utils.addPortalMessage(msg, type='info')

    def createDocument(self, conteudo, folder_conteudo):
        """
        """
        log = logging.getLogger('createDocument:')

        site = getSite()
        id_folder = queryUtility(IIDNormalizer).normalize(folder_conteudo)

        if not hasattr(site, id_folder):
            site.invokeFactory('Folder', id=id_folder, title=folder_conteudo)

        folderMediaWiki = getattr(site, id_folder)
        for i in conteudo:
            id = queryUtility(IIDNormalizer).normalize(i['title'])
            if not hasattr(folderMediaWiki, id):
                folderMediaWiki.invokeFactory('Document', id=id, title=i['title'])
                page = getattr(folderMediaWiki, id)
                page.setText(i['text'], mimetype='text/html')
                log.info(id)

    @memoize
    def validateTipoServico(self, tipo_servico, folder_catalogo):
        """Validação do tipo de serviço.
        """
        context = aq_inner(self.context)
        utils = getToolByName(context, 'plone_utils')
        ctool = getToolByName(context, 'portal_catalog')
        if (tipo_servico == ''):
            self.errors['tipo_servico'] = "O campo é obrigatório."
        if (folder_catalogo == ''):
            self.errors['folder_catalogo'] = "O campo é obrigatório."
        else:
            path = folder_catalogo.split('/')
            if path[-1] == '':
                id_folder = path[:-1][-1]
                path = '/'.join(path[:-2])
            else:
                id_folder = path[-1]
                path = '/'.join(path[:-1])
            folders = ctool(portal_type='Folder', id=id_folder, path={"query": path, "depth": 1})
            if not folders:
                self.errors['folder_catalogo'] = "Caminho não localizado. Favor informar uma caminho válido."
        # Check for errors
        if self.errors:
            utils.addPortalMessage("Corrija os erros.", type='error')
            return False
        else:
            return True

    def createAtividade(self, tipo_servico, folder_catalogo):
        """
        """
        log = logging.getLogger('createAtividade:')
        ctool = getToolByName(self.context, 'portal_catalog')
        #folder_conteudo = 'catalogo'
        site = getSite()
        pw = getToolByName(site, 'portal_workflow')
        publish = pw.doActionFor
        idnormalizer = queryUtility(IIDNormalizer)
        #id_folder = idnormalizer.normalize(folder_conteudo)
        path = folder_catalogo.split('/')
        if path[-1] == '':
            id_folder = path[:-1][-1]
            path = '/'.join(path[:-2])
        else:
            id_folder = path[-1]
            path = '/'.join(path[:-1])
        folder = ctool(portal_type='Folder', id=id_folder, path={"query": path, "depth": 1})[0]
        folderCASTI = folder.getObject()
        #if not hasattr(site, id_folder):
        #    site.invokeFactory('Folder', id=id_folder, title=folder_conteudo)
        #folderCASTI = getattr(site, id_folder)

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ICatalogoServicoPrefsForm)
        url = str(settings.url_webservice)
        client = Client(url)
        filtro = client.factory.create('wsFiltros')

        if tipo_servico == '1':
            filtro.tipoServico.id = 1
            filtro.tipoServico.sigla = "INFR"
            nome_servico = _(u'Infraestrutura')

        if tipo_servico == '2':
            filtro.tipoServico.id = 2
            filtro.tipoServico.sigla = "CRTL"
            nome_servico = _(u'Apoio ao Controle')

        if tipo_servico == '3':
            filtro.tipoServico.id = 3
            filtro.tipoServico.sigla = "SUST"
            nome_servico = _(u'Sustentação')

        if tipo_servico == '4':
            filtro.tipoServico.id = 4
            filtro.tipoServico.sigla = "PLAN"
            nome_servico = _(u'Apoio ao Planejamento')

        search = client.service.consultarAtividades(filtro)
        result = []

        id_processo = str(filtro.tipoServico.id) + '-' + idnormalizer.normalize(nome_servico)
        if not hasattr(folderCASTI, id_processo):
            folderCASTI.invokeFactory('Folder', id=id_processo, title=nome_servico)
            folderProcesso = getattr(folderCASTI, id_processo)
            folderProcesso.setLayout('lista-atividade')
            publish(folderProcesso, 'publish')
        else:
            folderProcesso = getattr(folderCASTI, id_processo)

        for item in search.item:
            title_subprocesso = item.codigo + ' - ' + item.descricao
            id_subprocesso = idnormalizer.normalize(title_subprocesso)

            if not hasattr(folderProcesso, id_subprocesso):
                folderProcesso.invokeFactory('Folder', id=id_subprocesso, title=title_subprocesso)
                folderSubProcesso = getattr(folderProcesso, id_subprocesso)
                folderSubProcesso.setLayout('lista-atividade')
                publish(folderSubProcesso, 'publish')

            for atividade in item.listAtividade:
                item = {'id': tipo_servico + '-' + item.codigo + '-' + atividade.codigo,
                        'codigo': atividade.codigo,
                        'descricao': atividade.descricao,
                        'subprocesso': id_subprocesso}
                result.append(item)

        for i in result:
            subprocesso = i['subprocesso']
            folderSubProcesso = getattr(folderProcesso, subprocesso)
            id = i['id']
            if not hasattr(folderSubProcesso, id):
                title_atividade = i['codigo'] + ' - ' + i['descricao']
                folderSubProcesso.invokeFactory('Atividade',
                                                id=id,
                                                title=title_atividade,
                                                codigo_atividade=i['codigo'],
                                                tipo_servico=tipo_servico,
                                                allowDiscussion=True)
                at = getattr(folderSubProcesso, id)
                publish(at, 'publish')
                log.info(id)

