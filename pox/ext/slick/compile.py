########################################
# This code can be used to compile a Slick Policy into an inermediate
# form such that we can compare it with other policies.
# And check a single policy for issues and rule breaks.
# Loops
# Wrong elements in the chain.
# Inter Policy:
# Flow overlaps.
#####################################
import ast
import astpp


class FuncCallLister(ast.NodeVisitor):
    def visit_Call(self, node):
        print "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        #print(node.func.args)
        #self.generic_visit(node)

class CompilePolicy():
    """Class to compile a single policy"""
    def __init__(self):
        self.policies = [ ] # List of policy filenames
        pass

    def __get_policy_filepath(self, policy_name):
        policy_filename = policy_name + ".py"
        policy_path = "apps/" + policy_filename
        #app_class = sys.modules['slick.apps.'+application].__dict__[application]
        print policy_path
        return policy_path
    
    def _read_code(self, policy_name):
        """Open code file and read it.
        Args: 
            policy_name: Name of the policy class as it appears in the code.
        Returns:
            Finds and reads the file and returns the policy code as string for AST to parse.
        """
        policy_file_path = self.__get_policy_filepath(policy_name)
        f = open(policy_file_path, 'r')
        policy_code_string = f.read()
        return policy_code_string

    def _represent_code(self, policy_code_string):
        """Walk the AST and represent the code as a kripke structure. or DAG.
        This function should be used to conver"""
        tree = ast.parse(policy_code_string)
        print astpp.dump(tree)
        FuncCallLister().visit(tree)
        print "AAAAAAAAAAAAAAAA"

    def _analyze_code(self, DAG):
        """Analyze all the paths of the DAG to see any violations for the policy
        rules."""
        pass

    def compile_policy(self, policy_name):
        policy_code = self._read_code(policy_name)
        code_intermediate_rep = self._represent_code(policy_code)
        self._analyze_code(code_intermediate_rep)

# Testing
def main():
    # Full path representing the policy filename.
    policy_name = "HttpLogger"
    comp_policy = CompilePolicy()
    comp_policy.compile_policy(policy_name)

if __name__ == "__main__":
    main()
