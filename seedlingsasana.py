import json
import csv
import os

from datetime import datetime
from Tkinter import *

import asana.client



class SeedlingsAsana:

    API_KEY = os.environ['ASANA_KEY']   # this environment variable needs to be set
    WORKSPACE_ID = '21476457590574' # The Seedlings workspace

    def __init__(self):
        self.client = asana.Client.basic_auth(self.API_KEY)

        self.projects = self.client\
                            .projects\
                            .find_by_workspace(self.WORKSPACE_ID, iterator_type=None)

        self.all_due_task_ids = None

        self.due_dates = {}

        self.due_task_map = {}
        self.due_tasknames = []

        self.due_contents = None

        # instead of looking up all the "Due" tasks every time the
        # script is run, we cache the results once and hope the ID's
        # don't change. If they do change, we can just run get_all_due()
        # again. Network latency makes this a pretty slow operation.
        if not os.path.isfile('.due_map'):
            self.get_all_due()
        else:
            self.read_due_map()

    def get_project(self, project_name):
        """
        Given a project name, like '06_11', this function returns the
        data associated with that project on the Asana server. This
        will include the project ID.

        :param project_name: name of visit, for example: '06_11'
        :return: dictionary containing asana id and name of the project

                for example:
                    {u'id': 37480810169333, u'name': u'06_11'}
        """
        result = None

        for project in self.projects:
            if project['name'] == project_name:
                result = project

        return result

    def get_all_task_ids(self, project_name):
        """
        Given the project name, like '06_11', this function returns
        a list of all task metadata associated with that project from
        the Asana server. The items in the list are dictionaries

        :param project_name: name of visit, for example: '06_11'
        :return: list containing the tasks, in dictionary form

                for example:
                           [{u'id': 37480810169336, u'name': u'General Notes:'},
                            {u'id': 37480810169337, u'name': u'06_11 Due'},
                            {u'id': 37480810169338, u'name': u'Processing:'},
                            {u'id': 37480810169339, u'name': u'Video Import'},
                            {u'id': 37480810169340, u'name': u'Video Processing'},
                            {u'id': 37480810169341, u'name': u'Audio Import'}],
                            ...
                            ...etc...
                            ...
                            {u'id': 37480810169366, u'name': u'Final File Organization'}]
        """
        project = self.get_project(project_name)
        tasks = self.client.tasks.find_by_project(project['id'])
        return tasks

    def get_all_tasks(self, tasks):
        """
        Given a list of task items (dictionaries containing task ID
        and name), this returns a list containing the contents of
        each task.

        :param tasks: list of task entries (e.g. {u'id': 37480810169337, u'name': u'06_11 Due'})
        :return result_tasks: list containing contents of each corresponding task.
        """

        result_tasks = []

        for task in tasks:
            result_tasks.append(self.client.tasks.find_by_id(task['id']))

        return result_tasks

    def get_all_due(self):
        """
        :return: a list of task entries for every task that has "Due" in the title
        """
        all_task_ids = []
        due_task_ids = []   # we're only going to keep the ones that are not completed

        # get all the tasks
        for project in self.projects:
            all_task_ids.append(self.get_all_task_ids(project['name']))

        # filter for the ones marked "Due"
        for project in all_task_ids:
            for task in project:
                if "Due" in task['name']:
                    task_contents = self.client.tasks.find_by_id(task['id'])
                    if task_contents['completed'] == False:
                        due_task_ids.append(task)

        self.all_due_task_ids = due_task_ids
        self.build_due_map(due_task_ids)

        return due_task_ids

    def build_due_map(self, tasks):

        with open('.due_map', 'w') as map_file:
            for entry in tasks:
                map_file.write("{},{}\n".format(entry['name'][0:5], entry['id']))

    def read_due_map(self):
        with open('.due_map', 'rU') as map_file:
            csvreader = csv.reader(map_file)
            for row in csvreader:
                self.due_task_map[row[0]] = row[1]
                self.due_tasknames.append(row[0])

    #def build_due_csv(self):



    # def build_due_dates(self):
    #     if self.all_due_task_ids:
    #
    #     else:
    #         due_tasks = self.get_all_due()
    #
    #     for task in due_tasks:
    #         self.due_dates[task['id']]
    #

class MainWindow:

    def __init__(self, master, asana_client):
        self.root = master
        self.root.title("Seedlings Asana")
        self.root.geometry("800x600")
        self.main_frame = Frame(self.root)
        self.main_frame.pack()

        self.client = asana_client  # SeedlingsAsana object

        # declare buttons
        self.load_due_button = Button(self.main_frame, text="Load Due", command=self.load_due)
        self.load_detail_button = Button(self.main_frame, text="Details", command=self.load_details)
        self.load_tasks_button = Button(self.main_frame, text="Load All Tasks", command=self.load_tasks)

        # grid() buttons
        self.load_due_button.grid(row=2, column=0)
        self.load_detail_button.grid(row=3, column=0)
        self.load_tasks_button.grid(row=4, column=0)

        # declare Labels
        self.info_label = Label(self.main_frame, text="Info")
        self.two_week_label = Label(self.main_frame, text="2 Week Tasks")
        self.one_month_label = Label(self.main_frame, text="1 Month Tasks")

        # grid() labels
        self.info_label.grid(row=0, column=1)
        self.two_week_label.grid(row=0, column=2)
        self.one_month_label.grid(row=0, column=3)

        self.due_box = Listbox(self.main_frame, width=15, height=27)
        self.detail_box = Listbox(self.main_frame, width=30, height=30)
        self.two_week_box = Listbox(self.main_frame, width=30, height=30)
        self.one_month_box = Listbox(self.main_frame, width=30, height=30)


        self.due_box.grid(row=1, column=0)
        self.detail_box.grid(row=1, column=1)
        self.two_week_box.grid(row=1, column=2)
        self.one_month_box.grid(row=1, column=3)

        self.due_ids = None     # just the task ID's
        self.due_tasks = None   # the content of the task in json

        self.two_week_tasks = {}
        self.one_month_tasks = {}


    def load_due(self):
        self.due_box.delete(0, END) # wipe the box first
        for index, due in enumerate(self.client.due_tasknames):
            self.due_box.insert(index, due)

    def load_incomplete(self):
        self.due_box.delete(0, END) # wipe the box first
        for index, due in enumerate(self.client.due_tasknames):
            self.due_box.insert(index, due)

    def load_details(self):
        task_name = self.client.due_tasknames[self.due_box.curselection()[0]]
        task_id = self.client.due_task_map[task_name]

        details = self.client.client.tasks.find_by_id(task_id)

        print json.dumps(details, indent=2)

        self.detail_box.delete(0, END)  # wipe the box
        self.detail_box.insert(0, "name:        {}".format(details['name']))
        self.detail_box.insert(1, "due:           {}".format(details['due_on']))
        self.detail_box.insert(2, "complete:  {}".format(details['completed']))

        #self.load_tasks(details['memberships'][0]['project']['name'])

        #self.detail_box.insert(1, self.client.)


    def load_tasks(self):
        """
        This loads all the tasks that are associated with the "XX_YY Due"
        task. So all the tasks in the XX_YY project will be pulled out
        :param parent_name: Name of the parent of the "Due" task, which should
        be the project as a whole.
        :return: list of json task entries from the associated project
        """

        task_ids = {}

        for due in self.client.due_task_map:
            task_ids[due] = self.client.client.get_all_task_ids(due)
        #ids = self.client.get_all_task_ids(parent_name)




if __name__ == "__main__":

    client = SeedlingsAsana()

    root = Tk()
    MainWindow(root, client)
    root.mainloop()



    # print "\nget_project: \n"
    # print client.get_project('06_11')
    #
    # print "\nget_tasks \n"
    # tasks = client.get_all_task_ids('06_11')
    #
    # for task in tasks:
    #     print task
    #
    # dues = client.get_all_due()
    # print "\n\ntasks due: \n"
    # for due in dues:
    #     print due

    test_dues = [{u'id': 37480810169337, u'name': u'06_11 Due'},
                 {u'id': 33302364234522, u'name': u'07_10 Due'},
                 {u'id': 28495144706461, u'name': u'08_08 Due'},
                 {u'id': 30927383779461, u'name': u'08_09 Due'},
                 {u'id': 36531056268390, u'name': u'07_11 Due'},
                 {u'id': 33477713328926, u'name': u'08_10 Due'},
                 {u'id': 29107428218920, u'name': u'09_08 Due'},
                 {u'id': 24328664284374, u'name': u'10_06 Due'},
                 {u'id': 27292237838355, u'name': u'10_07 Due'},
                 {u'id': 31608286218401, u'name': u'09_09 Due'},
                 {u'id': 29435185341333, u'name': u'10_08 Due'},
                 {u'id': 26206975565609, u'name': u'11_06 Due'},
                 {u'id': 27881353149354, u'name': u'11_07 Due'},
                 {u'id': 31964617909900, u'name': u'10_09 Due'},
                 {u'id': 26225856079844, u'name': u'12_06 Due'}
                ]

    # due_contents = client.get_all_tasks(test_dues)
    # due_dates = []
    #
    # for entry in due_contents:
    #     print json.dumps(entry, indent=2)
    #
    # for entry in due_contents:
    #     #dt_obj = datetime.strptime(dt_str, '%m/%d/%Y %I:%M:%S %p')
    #     due_dates.append(datetime.strptime(entry['due_on'], '%Y-%m-%d'))
    #
    #     print "due on: " + entry['due_on']
    #
    # print due_dates

    #client.get_all_due()
    # stuff = client.get_all_tasks(test_dues)
    # thing = client.get_project('28_06')
    #
    # thing_list = []
    #
    # thing_list.append(thing)
    #
    # stuff2 = client.get_all_task_ids('28_06')
    # stuff3 = client.get_all_tasks(stuff2)
    #
    #
    # print "stuff 3: \n"
    # print json.dumps(stuff3, indent=2)
    # print
    #
    # print
    # print
    # print thing
    # print
    #
    # print json.dumps(stuff, indent=2)



