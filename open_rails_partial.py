import sublime, sublime_plugin
import os.path, string
import re

# TODO: add compatibility for user.things, @user.things
# TODO: add compatibility for things, thing
# BUG: for quoted, when cursor in shared, doesn't work

VALID_FILENAME_CHARS = "-_.() %s%s%s" % (string.ascii_letters, string.digits, "/:\\")


# https://gist.github.com/1186126
class OpenRailsPartial(sublime_plugin.TextCommand):
    def run(self, edit):
        for region in self.view.sel():
            # get the current file extension
            syntax = self.view.scope_name(region.begin())
            if re.match("text.html.ruby*", syntax):
                extension = '.html.erb'
            elif re.match("text.haml*", syntax):
                extension = '.html.haml'
            else:
                extension = ''
            print "extension: " + extension

            # get the partial string or instance variable
            quoted_text = self.get_quoted_selection(region)
            print "quoted_text: " + quoted_text
            selected_text = self.get_selection(region)
            print "selected_text: " + selected_text
            current_string = self.get_current_string(region)
            print "current_string: " + current_string
            instance_text = self.remove_instance_identifier(current_string) if current_string else ''
            print "instance_text: " + instance_text
            # whole_line = self.get_line(region)
            # clipboard = sublime.get_clipboard().strip()

            # create file name from string/instance
            if quoted_text:
                new_filename = self.create_path_from_name(quoted_text, extension)
            elif selected_text:
                new_filename = self.create_path_from_name(selected_text, extension)
            elif instance_text:
                new_filename = self.create_path_from_instance(instance_text, extension)
            else:
                new_filename = ''
            print 'new_filename: ' + new_filename

            # Search for a valid filename from the possible sources: quoted_text, selected_text, whole_line, clipboard
            # If none of these sources match a valid filename the a new filename will be created from the selected_text
            # filename = new_filename
            # for text in (quoted_text, selected_text, whole_line, clipboard):
            found_filename = ''
            for text in (quoted_text, selected_text):
                potential_filename = self.name_to_path(text, extension)
                if os.path.isfile(potential_filename):
                    found_filename = potential_filename
                    break
            if selected_text:
                potential_filename = self.instance_to_path(selected_text, extension)
                if os.path.isfile(potential_filename):
                    found_filename = potential_filename
            elif instance_text:
                potential_filename = self.instance_to_path(instance_text, extension)
                # print potential_filename
                if os.path.isfile(potential_filename):
                    found_filename = potential_filename

            filename = found_filename if found_filename else new_filename

            # If a filename was discovered from one of the sources, then open it
            if filename:
                print "Opening file '%s'" % (filename)
                self.view.window().open_file(filename)
            else:
                print "No filename discovered in the quoted_text, selected_text, or current_string"

    def get_selection(self, region):
        return self.view.substr(region).strip()

    def get_current_string(self, region):
        return self.view.substr(self.view.extract_scope(region.begin())).strip()

    # def get_line(self, region):
    #     return self.view.substr(self.view.line(region)).strip()

    def get_quoted_selection(self, region):
        text = self.view.substr(self.view.extract_scope(region.begin()))
        position = self.view.rowcol(region.begin())[1]
        syntax = self.view.scope_name(region.begin())
        quoted_text = ''
        if re.match(".*string.quoted.double*", syntax):
            quoted_text = self.expand_within_quotes(text, position, '"')
            # print quoted_text
        elif re.match(".*string.quoted.single*", syntax):
            quoted_text = self.expand_within_quotes(text, position, '\'')
            # print quoted_text
        return quoted_text

    def expand_within_quotes(self, text, position, quote_character):
        close_quote = text.rfind(quote_character, 1, position)
        return text[1:close_quote] if (close_quote > 0) else ''

    def remove_instance_identifier(self, text):
        return text[1:] if text.startswith('@') | text.startswith('.') else text

    def instance_to_path(self, text, extension):
        current_dir = os.path.dirname(self.view.file_name())
        parent_dir = os.path.dirname(current_dir)
        partial = ''
        if text:
            if text.endswith('s'):
                partial = parent_dir + '/' + text + '/' + '_' + text[:-1] + extension
            else:
                partial = parent_dir + '/' + text + 's/' + '_' + text + extension
        return partial

    def name_to_path(self, text, extension):
        current_dir = os.path.dirname(self.view.file_name())
        parent_dir = os.path.dirname(current_dir)
        file_array = text.split('/')
        count = len(file_array)
        if count == 1:
            partial = current_dir + '/' + '_' + text + extension
            # print partial
        else:
            new_filename = '_' + file_array[(count - 1)] + extension
            file_array.pop()
            file_array.append(new_filename)
            partial = parent_dir + '/' + ('/').join(file_array)
        return partial

    # def name_to_path(self, text, extension):
    #     current_dir = os.path.dirname(self.view.file_name())
    #     # parent_dir = os.path.dirname(current_dir)
    #     stripped = text.strip()
    #     # file_array = stripped.split('/')
    #     # count = len(file_array)
    #     normal = current_dir + '/' + stripped
    #     partial = self.name_to_path(stripped, extension)
    #     if os.path.isfile(normal):
    #         return text
    #     elif os.path.isfile(partial):
    #         # print 'partial is found'
    #         return partial
    #     else:
    #         return ''

    # def check_if_exists(self, path):
    #     return path if os.path.isfile(path) else ''

    def create_path_from_name(self, text, extension):
        stripped = text.strip()
        partial = self.name_to_path(stripped, extension)
        if text:
            return ''.join(c for c in partial if c in VALID_FILENAME_CHARS)
        else:
            return ''

    def create_path_from_instance(self, text, extension):
        stripped = text.strip()
        partial = self.instance_to_path(stripped, extension)
        if text:
            return ''.join(c for c in partial if c in VALID_FILENAME_CHARS)
        else:
            return ''
