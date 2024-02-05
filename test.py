import os, sys, re, json
import requests

def create_new_contact(first_name, username, phone):
	data = {
		"fields": {
			"NAME"			: "Vlad (DEV)",
			"PHONE"			: [{"VALUE": phone}],
			"SOURCE_ID" 	: "UC_FENJGP",
		}
	}
	response = requests.post("https://interhash.bitrix24.ru/rest/26/2fbqa7d1gkru4wft/crm.contact.add.json?", json = data, headers = {"Content-Type": "application/json"})
	if response.status_code == 200:
		contact = response.json()
		return {'id': contact['result']}


def create_crm_param(name_chat, name_sender, comments, contact_id):
	data = {
		"fields": {
			"UF_CRM_1705409893052"	: name_chat,
			"UF_CRM_1652807468307" 	: name_sender,
			"CATEGORY_ID" 			: 0,
			"STATUS_ID"				: "NEW",
			"SOURCE_ID" 			: "UC_FENJGP",
			"COMMENTS"				: str(comments),
			"ASSIGNED_BY_ID"		: 2098,
			"CONTACT_ID" 			: contact_id,
		},
	}
	return data



url_message = "t.me/testpublicgroup12/307"

contact = create_new_contact(first_name = "Vlad", username = "cayse", phone = str(380990000228))

event = "Affected by the LTC pool server upgrade, the LTC mining revenue payment was delayed on 01-28 and is now scheduled to commence on 2024-01-29. Please note that LTC mining activities remain unaffected, and any rewards during this period will accrue in your account balance."

text = '<br>'.join([
    "<b>● Chat Name: </b>" + "Name of chat",
    "<b>● Chat ID: </b>" + str(123456789),
    "",
    "<b>● Name: </b>" + "Vlad",
    "<b>● Last Name: </b>" + "None",
    "<b>● User ID: </b>" + str(123),
    "<b>● Username: </b>" + "<a href=t.me/cayse}>@cayse</a>",
    "<b>● Phone: </b>" + str(380990000228),
    "",
    "<b>● Message: </b>" + str("<i>'" + event + "'</i>"),
    "<b>● Keys: </b><i>" + "#kto_suka_delete_webhook?</i>",
    "",
    f"<a href={url_message}>{url_message}</a>",
    ])


data = create_crm_param(name_chat = "Name of chat", name_sender = "Vlad (DEV)", comments = text, contact_id = contact['id'])

crm = requests.post("https://interhash.bitrix24.ru/rest/26/2fbqa7d1gkru4wft/crm.deal.add.json?", json = data, headers = {"Content-Type": "application/json"})

print(crm.status_code)
print()
print(crm.text)