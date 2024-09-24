#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_google.provider import GoogleProvider
from cdktf_cdktf_provider_google.project_iam_binding import ProjectIamBinding
import mysql.connector

db = mysql.connector.connect(
    host='db.ip',
    port='3306',
    user='user',
    passwd='password',
    database='database'
)

def SqlFrontdoor(project: str, *data: tuple ):
    TableCreate = "CREATE TABLE IF NOT EXISTS {0} (members VARCHAR(255), role VARCHAR(255))" .format(project)
    TableInsert = "INSERT IGNORE INTO {0} (members, role) VALUES (%s, %s)" .format(project)
    TableSelect = "SELECT * FROM {0}" .format(project)
    fakepayload = [("group:admins@corp.com", "admin"),
                   ("serviceAccount:app@appspot.gserviceaccount.com", "developer"),
                   ("domain:corp.com", "reader")
                   ]
    cursor = db.cursor()
    cursor.execute(TableCreate)
    cursor.execute(TableSelect)
    preload = cursor.fetchall()
    massage = list(set(fakepayload) - set(preload))
    cursor.executemany(TableInsert, massage)
    db.commit()
    cursor.execute(TableSelect)
    postload = cursor.fetchall()

    return postload

def CommonRole(Payload):
    NewList = {}
    for user, role in Payload:
        NewList.setdefault(role, []).append(user)

    return NewList

class IamBinding(TerraformStack):
    def __init__(self, scope: Construct, id: str, payload):
        super().__init__(scope, id)

        GoogleProvider(self, "GCP", region="northamerica-northeast-1", project=id)
        for key in payload:
            ProjectIamBinding(self, key, project=id, members=payload[key], role=key)

prj = 'project123'
database = SqlFrontdoor(prj, 'blank')
Restructure = CommonRole(database)
print(Restructure)
app = App()
IamBinding(app, prj, Restructure)
app.synth()
