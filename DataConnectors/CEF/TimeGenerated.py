import subprocess
import sys

oms_agent_field_mapping_configuration = "/opt/microsoft/omsagent/plugin/filter_syslog_security.rb"
oms_agent_service_control = "/opt/microsoft/omsagent/bin/service_control"
yes_response = ["Yes", "YES", "yes", "Y", "y"]


def print_ok(input_str):
    print("\033[1;32;40m" + input_str + "\033[0m")


def print_error(input_str):
    print("\033[1;31;40m" + input_str + "\033[0m")


def print_notice(input_str):
    print("\033[0;30;47m" + input_str + "\033[0m")


def prompt_messages():
    """
    Prompt the user for opening messages and
    :return: the workspace id of the user if he wants to change the timestamp
    """
    ws_id = 0
    if check_logs_timestamp():
        input_message = "would you like to change the log timestamp from log collection time to log creation time?" \
                        "\nEnter Yes/No\n"
        print_notice("We have recognized your logs timestamp is set to: Log collection time\n")
    else:
        input_message = "would you like to change the log timestamp from log creation time to log collection time?" \
                        "\nEnter Yes/No\n"
        print_notice("We have recognized your logs timestamp is set to: Log creation time\n")
    # to be compatible with both python 2.7 and python 3
    try:
        response = raw_input(input_message)
        if response in yes_response:
            ws_id = raw_input("Please enter your Workspace ID:\n")
    except NameError:
        response = input(input_message)
        if response in yes_response:
            ws_id = input("Please enter your Workspace ID:\n")
    return ws_id


def is_logs_collection_time():
    """
    :return: True if current timegenerated configuration is set to log collection time
    """
    grep = subprocess.Popen(["grep", "-i", "'Timestamp' => OMS::Common::fast_utc_to_iso8601_format(Time.now.utc),",
                             oms_agent_field_mapping_configuration], stdout=subprocess.PIPE)
    o, e = grep.communicate()
    output_decode = o.decode(encoding='UTF-8')
    if e is not None:
        print_error("Couldn't locate TimeGenerated configuration")
        sys.exit()
    if output_decode is not None and output_decode != "":
        return True
    return False


def is_logs_creation_time():
    """
    :return: True if current timegenerated configuration is set to log creation time
    """
    grep = subprocess.Popen(["grep", "-i", "'Timestamp' => OMS::Common::fast_utc_to_iso8601_format(Time.at(time).utc),",
                             oms_agent_field_mapping_configuration], stdout=subprocess.PIPE)
    o, e = grep.communicate()
    output_decode = o.decode(encoding='UTF-8')
    if e is not None:
        print_error("Couldn't locate TimeGenerated configuration")
        sys.exit()
    if output_decode is not None and output_decode != "":
        return True
    return False


def check_logs_timestamp():
    # True if log collection time, False if log creation time
    if is_logs_collection_time():
        return True
    if is_logs_creation_time():
        return False
    print_error("No valid logs timestamp found")
    sys.exit()


def change_events_timegenerated():
    """
    :return: True if successfully changed the TimeGenerated configuration
    """
    collect_to_create = "s|'Timestamp' => OMS::Common::fast_utc_to_iso8601_format(Time.now.utc),|'Timestamp' =>" \
                        " OMS::Common::fast_utc_to_iso8601_format(Time.at(time).utc),|g"
    create_to_collect = "s|'Timestamp' => OMS::Common::fast_utc_to_iso8601_format(Time.at(time).utc),|'Timestamp' =>" \
                        " OMS::Common::fast_utc_to_iso8601_format(Time.now.utc),|g"
    print_notice(
        "Ateempting to change TimeGenerated configuration configuration")
    if check_logs_timestamp():
        sed = subprocess.Popen(["sed", "-i", collect_to_create,
                                oms_agent_field_mapping_configuration], stdout=subprocess.PIPE)
    else:
        sed = subprocess.Popen(["sed", "-i", create_to_collect,
                                oms_agent_field_mapping_configuration], stdout=subprocess.PIPE)
    o, e = sed.communicate()
    if e is not None:
        print_error("Failed to change log TimeGenerated configuration")
        return False
    print_ok("Successfully changed log TimeGenerated configuration")
    return True


def restart_omsagent(workspace_id):
    print_notice("Attempting to restart the OMS agent")
    agent_restart = subprocess.Popen(["sudo", oms_agent_service_control, "restart", workspace_id],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    o, e = agent_restart.communicate()
    error_decode = e.decode(encoding='UTF-8')
    if error_decode is not None and error_decode != "":
        print_error("Failed to restart the OMS agent")
        sys.exit()
    print_ok("Successfully restart the OMS agent")


def main():
    ws_id = prompt_messages()
    if ws_id == 0:
        print_notice("Exiting script")
        sys.exit()
    change_events_timegenerated()
    restart_omsagent(ws_id)


if __name__ == '__main__':
    main()
