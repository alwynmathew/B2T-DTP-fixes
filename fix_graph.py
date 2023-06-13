# -*- coding: utf-8 -*-`

# Copyright University of Cambridge 2023. All Rights Reserved.
# Author: Alwyn Mathew <am3156@cam.ac.uk>
# This file cannot be used without a written permission from the author(s).

import argparse
import os

import yaml
from tqdm import tqdm

from DTP_API.DTP_API import DTPApi
from DTP_API.DTP_config import DTPConfig


class FixDTPGraph:
    """
    The class is used to prepare DTP for progress monitering

    Attributes
    ----------
    DTP_CONFIG : class
        an instance of DTP_Config
    DTP_API : DTP_Api, obligatory
            an instance of DTP_Api

    Methods
    -------
    update_asplanned_dtp_nodes()
        int, returns number of nodes updated
    """

    def __init__(self, dtp_config, dtp_api):
        """
        Parameters
        ----------
        dtp_config : DTP_Config, obligatory
            an instance of DTP_Config
        dtp_api : DTP_Api, obligatory
            an instance of DTP_Api
        """
        self.DTP_CONFIG = dtp_config
        self.DTP_API = dtp_api

    def __fetch_all_element_nodes(self):
        """
        The method fetch all element nodes including as-planned and as-performed

        Returns
        -------
        dict
            Dictionary of elements
        """
        all_elements = self.DTP_API.fetch_element_nodes()
        elements = all_elements
        while 'next' in elements.keys() and elements['size'] != 0:
            elements = self.DTP_API.fetch_element_nodes(elements['next'])
            if elements['size'] <= 0:
                break
            all_elements['items'] += elements['items']
            all_elements['size'] += elements['size']

        return all_elements

    def __filter_asplanned(self, all_element):
        """

        Parameters
        ----------
        all_element : dict, obligatory
            Dictionary of all element nodes
        Returns
        -------
        dict
            Dictionary of filtered elements into as-planned and as-performed
        """
        filtered_node = {'as_planned': []}
        as_designed_uri = self.DTP_CONFIG.get_ontology_uri('isAsDesigned')
        for each_dict in all_element['items']:
            if as_designed_uri not in each_dict.keys() or each_dict[as_designed_uri] is True:
                filtered_node['as_planned'].append(each_dict['_iri'])
                if 'ifc:Class' in each_dict:
                    filtered_node['as_planned'].append([each_dict['_iri'], each_dict['ifc:Class']])

        return filtered_node

    def __update_node(self, iri, prev_ifc_class_value, convert_maps):
        new_ifc_class_value = convert_maps[prev_ifc_class_value]
        delete_resp = self.DTP_API.delete_param_in_node(node_iri=iri, field="ifc:Class",
                                                        previous_field_value=prev_ifc_class_value)
        if delete_resp:
            add_resp = self.DTP_API.add_param_in_node(node_iri=iri,
                                                      field=self.DTP_CONFIG.get_ontology_uri('hasElementType'),
                                                      field_value=new_ifc_class_value)

            return True if delete_resp and add_resp else False
        else:
            return False

    def update_asplanned_dtp_nodes(self, convert_maps):
        """
        Updates AsDesigned parameter in as-planned element nodes

        Returns
        -------
        int
            The number of updated nodes
        convert_maps
            mapping from old ontology to new
        """
        num_updates = 0
        all_element = self.DTP_API.query_all_pages(self.DTP_API.fetch_element_nodes)
        filtered_nodes = self.__filter_asplanned(all_element)
        for as_planned in tqdm(filtered_nodes['as_planned']):
            # update IfcClass field
            if isinstance(as_planned, list):
                iri, prev_ifc_class_value = as_planned
                # some classes are ignored
                if convert_maps[prev_ifc_class_value] == 'ignore':
                    continue
                update_resp = self.__update_node(iri, prev_ifc_class_value, convert_maps)
                if not update_resp:
                    continue
            else:
                # update asDesigned field
                self.DTP_API.update_asdesigned_param_node(as_planned, is_as_designed=True)
            num_updates += 1
        return num_updates


def parse_args():
    """
    Get parameters from user
    """
    parser = argparse.ArgumentParser(description='Fix DTP graph')
    parser.add_argument('--simulation', '-s', default=False, action='store_true')
    parser.add_argument('--log_dir', '-l', type=str, help='path to log dir', required=True)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.simulation:
        print('Running in the simulator mode.')
    if not os.path.exists(args.log_dir):
        os.makedirs(args.log_dir)
    dtp_config = DTPConfig('DTP_API/DTP_config.xml')
    dtp_api = DTPApi(dtp_config, simulation_mode=args.simulation)
    prepareDTP = FixDTPGraph(dtp_config, dtp_api)
    ontology_map = yaml.safe_load(open('ontology_map.yaml'))
    num_element = prepareDTP.update_asplanned_dtp_nodes(ontology_map)
    print('Number of updated element', num_element)
