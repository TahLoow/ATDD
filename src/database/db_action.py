"""This class is a simple helper to standardize generate/load actions"""


class DbAction:
    """
    This class is a simple helper to standardize generate/load actions

    :param action_string: The GENERATE/LOAD command
    :type action_string: str
    """
    GENERATE = 0
    LOAD = 1
    state = None

    action_names = {
        GENERATE: 'Generate',
        LOAD: 'Load'
    }

    verb_mappings = {
        GENERATE: 'Generating',
        LOAD: 'Loading'
    }

    def __init__(self, action_string):
        """
        Constructor Method
        """
        self.state = self._cast_state_to_int(action_string)
        if self.state is None:
            raise ValueError(f'Invalid Database Action: {action_string}')

    def __str__(self):
        """
        Returns action names given a state
        :return: action_names
        :rtype: str
        """
        return self.action_names[self.state]

    def _cast_state_to_int(self, action_string):
        """
        converts GENERATE/LOAD string into 0 or 1, respectively
        :param action_string: The GENERATE/LOAD command
        :type action_string: str
        :return: result
        :rtype: int
        """
        action_string = str.lower(str(action_string)).lstrip("-")
        result = None

        if action_string == 'generate' or action_string == 'g' or action_string == '0':
            result = self.GENERATE
        elif action_string == 'load' or action_string == 'l' or action_string == '1':
            result = self.LOAD
        else:
            # Invalid state; will be None
            pass

        return result

    def is_generate(self):
        return self.state == self.GENERATE

    def is_load(self):
        return self.state == self.LOAD

    def shares_state(self, query_db_action):
        if type(query_db_action) == DbAction:
            return self.state == query_db_action.state
        else:
            return False

    def to_verb(self):
        """
        Converts the GENERATE/LOAD word into generate/load, respectively
        :return: the verb equivalent of the command
        :rtype: str
        """
        return self.verb_mappings[self.state]


if __name__ == '__main__':
    generate1 = DbAction('-g')
    generate2 = DbAction('generate')
    generate3 = DbAction('GENERATE')

    load1 = DbAction('-l')
    load2 = DbAction('load')
    load3 = DbAction('LOAD')

    print('Rudimentary testing')
    print('Should be true:')
    print(generate1.is_generate())
    print(generate2.is_generate())
    print(generate3.is_generate())

    print(load1.is_load())
    print(load2.is_load())
    print(load3.is_load())

    print('Should be false:')
    print(generate1.is_load())
    print(generate2.is_load())
    print(generate3.is_load())

    print(load1.is_generate())
    print(load2.is_generate())
    print(load3.is_generate())
