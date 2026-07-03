from pythonforandroid.recipe import CompiledComponentsPythonRecipe


class PymunkRecipe(CompiledComponentsPythonRecipe):
    """
    Recipe to build pymunk for Android.
    Pymunk uses CFFI to compile the Chipmunk physics library from source.
    This recipe extends the upstream p4a recipe with a modern pymunk version.
    """

    name = "pymunk"
    version = "7.3.0"
    url = "https://github.com/viblo/pymunk/archive/refs/tags/{version}.tar.gz"

    depends = ["cffi", "setuptools"]

    call_hostpython_via_targetpython = False

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env["LDFLAGS"] = env.get("LDFLAGS", "") + " -llog"
        env["LDFLAGS"] += " -lm"
        return env


recipe = PymunkRecipe()
