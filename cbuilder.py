import os
import re
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table

def clear_screen(): 
    # Windows 
    if os.name == 'nt': 
        _ = os.system('cls') 
    # Unix/Posix 
    else: 
        _ = os.system('clear') 

PRAGMA_ONCE_DEFINITION = '#pragma once\n'

g_project_name = None
g_current_module = None

'''
Structure containing the name and the documentation for a C++ function.
'''
class CFunction:
    def __init__(self, name, description) -> None:
        self.name = name
        self.description = description

'''
CClass is a template class for holding C++ project classes within a specific module.
It is able to hold public and private function names and variable names.
'''
class CClass:
    def __init__(self, name = 'class1') -> None:
        self.name = name
        self.public_functions: list[CFunction]   = []
        self.private_functions: list[CFunction]  = []
        self.public_variables   = []
        self.private_variables  = []

    def __get_header_function_declaration(self, fn) -> str:
        result = ''

        # Write the function comment if neccessary
        if fn.description != None:
            result += '\t\t/*\n\t\t\t{}\n\t\t*/\n'.format(fn.description.replace('\n', '\n\t\t\t'))

        # Write the function declaration
        result += '\t\tvoid {}();\n'.format(fn.name)

        # To make the spacing look good, if there was comment,
        # add a new line after the function declaration as well.
        if fn.description != None:
            result += '\n'

        return result

    # Generates a C++ header file (.h)
    def __generate_header_file(self) -> None:
        global g_project_name, g_current_module

        with open(self.name + '.h', 'w') as f:
            # Pragma + includes
            f.write(PRAGMA_ONCE_DEFINITION)

            # Namespace begin
            f.write('\nnamespace {}::{}\n{{\n'.format(g_project_name, g_current_module))

            # Class begin
            f.write('\tclass {}\n'.format(self.name))
            f.write('\t{')

            # Public functions
            if len(self.public_functions) > 0:
                f.write('\n')
                f.write('\tpublic:\n')

                for fn in self.public_functions:
                    code = self.__get_header_function_declaration(fn)
                    f.write(code)

            # Public variables
            if len(self.public_variables) > 0:
                f.write('\n')
                f.write('\tpublic:\n')
                
                for var in self.public_variables:
                    f.write('\t\t{};\n'.format(var))

            # Private functions
            if len(self.private_functions) > 0:
                f.write('\n')
                f.write('\tprivate:\n')

                for fn in self.public_functions:
                    code = self.__get_header_function_declaration(fn)
                    f.write(code)

            # Private variables
            if len(self.private_variables) > 0:
                f.write('\n')
                f.write('\tprivate:\n')
                
                for var in self.public_variables:
                    f.write('\t\t{};\n'.format(var))

            # Private functions
            f.write('\n')

            # Class end
            f.write('\t};\n')

            # Namespace end
            f.write('}\n')


    # Generates a C++ source file (.cpp)
    def __generate_source_file(self) -> None:
        global g_project_name, g_current_module

        with open(self.name + '.cpp', 'w') as f:
            f.write('#include "{}"\n\n'.format(self.name + '.h'))

            # Namespace begin
            f.write('namespace {}::{}\n{{\n'.format(g_project_name, g_current_module))

            # Namespace end
            f.write('}\n')

    # Generates a set of header and source files
    def generate_class_files(self):
        self.__generate_header_file()
        self.__generate_source_file()

'''
CModule is essentially a C++ namespace. It encapsulates classes
for a specific subsystem within a project.
'''
class CModule:
    def __init__(self, name = 'module1') -> None:
        self.name = name
        self.classes: list[CClass] = []

    # Returns a class with the given name
    def get_class(self, name) -> CClass:
        for cppclass in self.classes:
            if cppclass.name == name:
                return cppclass

        return None

     # Removes a class with the given name
    def remove_class(self, name) -> None:
        for cppclass in self.classes:
            if cppclass.name == name:
                self.classes.remove(cppclass)
                break

    # Creates the appropriate directory structure and
    # child C++ class header and source files on the disk.
    def generate_cpp_source_files(self) -> None:
        global g_current_module

        # Set the current module
        g_current_module = self.name

        # Create the directory for the module
        os.mkdir(self.name)

        # Enter the module directory
        os.chdir(self.name)

        # Iterate over every class in the module and
        # call its function to generate source files.
        for cppclass in self.classes:
            cppclass.generate_class_files()

        # Exit back from the module directory
        os.chdir('..')

        # Set the current module to None as we are done working with it
        g_current_module = None

'''
The main class that holds all the information about the project
on the highest level, i.e. which modules and subsystems exist within the project,
and other configuration parameters.
'''
class CProject:
    def __init__(self, name = 'project1', cppnamespace = '') -> None:
        # Initialize the name of the project
        self.name = name

        # Initialize the project c++ namespace
        if len(cppnamespace) > 0:
            self.cppnamespace = cppnamespace
        else:
            self.cppnamespace = name

        # Initialize the list of modules that the project contains
        self.modules: list[CModule] = []

    # Returns a CModule object given the module name
    def get_module(self, name) -> CModule:
        for mod in self.modules:
            if mod.name == name:
                return mod
        
        return None

    # Removes a module with the given name
    def remove_module(self, name) -> None:
        for mod in self.modules:
            if mod.name == name:
                self.modules.remove(mod)
                break

    # Generates C++ source files for each module and class
    def __generate_source_files(self) -> None:
        for mod in self.modules:
            mod.generate_cpp_source_files()

    # Generates the CMakeLists.txt files
    # for the project directory and nested modules.
    def __generate_cmake_file(self) -> None:
        pass

    # Primary function for processing all
    # the project details and subsystems and
    # creating the physical project in the filesystem.
    def generate_project(self, target_dir) -> None:
        global g_project_name

        # Set the project name global
        g_project_name = self.name

        # Get the absolute path (also fixes platform-dependent backslashes on windows)
        target_dir = os.path.abspath(target_dir)

        # Check if project parent directory exists
        if not os.path.isdir(target_dir):
            print('Error> target directory does not exist')
            return

        # Move into the target directory
        os.chdir(target_dir)

        # Check if project directory already exists
        if os.path.isdir(self.name):
            print('Error> project directory already exists')
            return

        # Create a new directory for the project
        os.mkdir(self.name)
        os.chdir(self.name)

        # Generate project source files on the disk
        self.__generate_source_files()

        # Create required CMake files
        self.__generate_cmake_file()

def render_project_table(console, project: CProject) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Project Name", style="bright", min_width=16)
    table.add_column("Modules", min_width=26)
    table.add_row(project.name)
    
    for mod in project.modules:
        table.add_row('', mod.name)

    console.print(table)
    console.print()

def render_module_table(console, module: CModule) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Module Name", style="bright", min_width=16)
    table.add_column("Classes",  min_width=26)
    table.add_row(module.name)
    
    for cppclass in module.classes:
        table.add_row('', cppclass.name)

    console.print(table)
    console.print()

def render_class_table(console, cppclass: CClass) -> None:
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Class Name", style="bright", min_width=16)
    table.add_column("Functions",  min_width=26)
    table.add_column("Members Variables",  min_width=26)
    table.add_row(cppclass.name)

    # Creating a single list that contains
    # both public and private functions.
    all_fns = [fn.name for fn in cppclass.public_functions]
    all_fns.extend([fn.name for fn in cppclass.private_functions])

    # Creating a single list that contains
    # both public and private variables.
    all_vars = [var for var in cppclass.public_variables]
    all_vars.extend([var for var in cppclass.private_variables])

    greatest_member_count = max(len(all_fns), len(all_vars))

    for i in range(0, greatest_member_count):
        fn = ''
        if i < len(all_fns):
            fn = all_fns[i]
            fn_type = 'public'
            if i >= len(cppclass.public_functions):
                fn_type = 'private'

        var = ''
        if i < len(all_vars):
            var = all_vars[i]
            var_type = 'public'
            if i >= len(cppclass.public_variables):
                var_type = 'private'

        table.add_row('', '{} ({})'.format(fn, fn_type), '{} ({})'.format(var, var_type))

    console.print(table)
    console.print()

def show_class_controls(console, cppclass: CClass):
    try:
        while True:
            render_class_table(console, cppclass)
            
            console.print('[1] Add function')
            console.print('[2] Remove function')
            console.print('[3] Add variable')
            console.print('[4] Remove variable')
            console.print('[5] Edit class name')
            console.print('[6] Return to module menu')
            console.print()

            user_cmd = int(Prompt.ask('Select option', choices=['1','2','3','4','5','6']))
            if user_cmd == 6: # return to project menu
               return

            clear_screen()
    except KeyboardInterrupt:
        return

def show_module_controls(console, module: CModule):
    try:
        while True:
            render_module_table(console, module)
            
            console.print('[1] Select class')
            console.print('[2] Add class')
            console.print('[3] Remove class')
            console.print('[4] Edit module name')
            console.print('[5] Return to project menu')
            console.print()

            user_cmd = int(Prompt.ask('Select option', choices=['1','2','3','4','5']))
            if user_cmd == 5: # return to project menu
               return

            # Select a class
            if user_cmd == 1 and len(module.classes) > 0:
                class_choices = [cppclass.name for cppclass in module.classes]
                selected_class_name = Prompt.ask('Enter class name', choices=class_choices)
                
                clear_screen()
                show_class_controls(console, module.get_class(selected_class_name))

            # Add class
            elif user_cmd == 2:
                console.print('New class name', style='cyan', end='')
                class_name = Prompt.ask('').replace(' ', '_')
                class_name = re.sub(r'[^a-zA-Z0-9_]', '', class_name) # remove all the non-alphanumeric characters
                module.classes.append(CClass(class_name))

            # Remove class
            elif user_cmd == 3:
                console.print('Enter class name', style='cyan', end='')
                class_name = Prompt.ask('').replace(' ', '_')
                class_name = re.sub(r'[^a-zA-Z0-9_]', '', class_name) # remove all the non-alphanumeric characters
                module.remove_class(class_name)

            # Edit module name
            elif user_cmd == 4:
                console.print('Enter new module name', style='cyan', end='')
                new_name = Prompt.ask('').replace(' ', '_')
                new_name = re.sub(r'[^a-zA-Z0-9_]', '', new_name) # remove all the non-alphanumeric characters
                module.name = new_name

            clear_screen()
    except KeyboardInterrupt:
        return

def show_project_controls(console, project: CProject) -> None:
    while True:
        try:
            render_project_table(console, project)
            
            console.print('[1] Select module')
            console.print('[2] Add module')
            console.print('[3] Remove module')
            console.print('[4] Edit project name')
            console.print('[5] Generate project')
            console.print('[6] Exit')
            console.print()

            user_cmd = int(Prompt.ask('Select option', choices=['1','2','3','4','5','6']))
            if user_cmd == 6: # exit
               if Confirm.ask('Are you sure you want to exit?'):
                   return

            # Select module
            if user_cmd == 1 and len(project.modules) > 0:
                module_choices = [mod.name for mod in project.modules]
                selected_module_name = Prompt.ask('Enter module name', choices=module_choices)
                
                clear_screen()
                show_module_controls(console, project.get_module(selected_module_name))

            # Add module
            elif user_cmd == 2:
                console.print('New module name', style='cyan', end='')
                mod_name = Prompt.ask('').replace(' ', '_')
                mod_name = re.sub(r'[^a-zA-Z0-9_]', '', mod_name) # remove all the non-alphanumeric characters
                project.modules.append(CModule(mod_name))

            # Remove module
            elif user_cmd == 3:
                console.print('Enter module name', style='cyan', end='')
                mod_name = Prompt.ask('').replace(' ', '_')
                mod_name = re.sub(r'[^a-zA-Z0-9_]', '', mod_name) # remove all the non-alphanumeric characters
                project.remove_module(mod_name)

            # Edit project name
            elif user_cmd == 4:
                console.print('Enter new project name', style='cyan', end='')
                new_name = Prompt.ask('').replace(' ', '_')
                new_name = re.sub(r'[^a-zA-Z0-9_]', '', new_name) # remove all the non-alphanumeric characters
                project.name = new_name

            clear_screen()

        except KeyboardInterrupt:
            console.print()
            if Confirm.ask('Are you sure you want to exit?'):
                return
            else:
                clear_screen()

def main() -> None:
    clear_screen()

    console = Console()
    console.print('\n', end='')
    console.print('Enter the project name', end='', style='cyan')

    project = CProject(Prompt.ask(''))
    clear_screen()

    client_app_class= CClass('client_app')
    client_app_class.public_functions.append(CFunction('render_app', 'Main rendering routine used to render the application'))
    client_app_class.public_functions.append(CFunction('render_overlay', 'Draws the 2D overlay over the main window'))
    client_app_class.public_variables.append('std::unique_ptr<ClientState> m_ClientState = nullptr')
    client_app_class.private_functions.append(CFunction('render_background_color', None))
    client_app_class.private_variables.append('Renderer* m_Renderer')
    client_app_class.private_variables.append('Window* m_Window')

    ui_module = CModule('ui')
    ui_module.classes.append(client_app_class)
    ui_module.classes.append(CClass('panels'))

    network_module = CModule('network')
    network_module.classes.append(CClass('Packets'))
    network_module.classes.append(CClass('NetworkManager'))

    utils_module = CModule('utils')
    utils_module.classes.append(CClass('Logger'))

    project.modules.append(ui_module)
    project.modules.append(network_module)
    project.modules.append(utils_module)

    show_project_controls(console, project)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

    print()