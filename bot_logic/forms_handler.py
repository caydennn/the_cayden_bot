

def handle_arts_fiesta(info):
    if info['action'] == 'test':
        inst_1 = info["instalment_1"]
        inst_2 = info["instalment_2"]
        return f"""
        This is a test message\. 
*Updates for Arts Fiesta Audience Registration Form*
Inst 1 Numbers: *{inst_1}*/200 people attending
Inst 2 Numbers: *{inst_2}*/200 people attending

Access the responses [here](https://sutdapac-my.sharepoint.com/:x:/r/personal/arts_rep_sutd_edu_sg/_layouts/15/Doc.aspx?sourcedoc=%7B7A09F250-B622-4013-9C69-2DE624375C83%7D&file=Arts%20Fiesta%20Audience%20Registration%20Responses.xlsx&action=edit&mobileredirect=true&d=w7a09f250b62240139c692de624375c83)\.
        """
    if info['action'] == 'count_instalment_numbers':
        inst_1 = info["instalment_1"]
        inst_2 = info["instalment_2"]
        inst_1 = int(inst_1)
        inst_2 = int(inst_2)
        # Only update if above 100 and multiple of 25
        if (inst_1 >= 100 and inst_1%25 == 0) or (inst_2 >= 100 and inst_2%25 == 0):
          return f"""
        *Updates for Arts Fiesta Audience Registration Form*
Inst 1 Numbers: *{inst_1}*/200 people attending
Inst 2 Numbers: *{inst_2}*/200 people attending

Access the responses [here](https://sutdapac-my.sharepoint.com/:x:/r/personal/arts_rep_sutd_edu_sg/_layouts/15/Doc.aspx?sourcedoc=%7B7A09F250-B622-4013-9C69-2DE624375C83%7D&file=Arts%20Fiesta%20Audience%20Registration%20Responses.xlsx&action=edit&mobileredirect=true&d=w7a09f250b62240139c692de624375c83)\.
        """
        else:
            return
