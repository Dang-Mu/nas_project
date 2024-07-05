from tutorial_code import tutorial
exp = tutorial()
print(exp)

# import atexit
# from nni.experiment import RunMode

# wait_completion = False
# run_mode = RunMode.Background

# if run_mode is not RunMode.Detach:
#     print(atexit.register(exp.stop))
# if exp._nni_manager_required():
#     if run_mode != RunMode.Background and exp._action in ['create', 'resume']:
#         print(run_mode)
# print(exp._action)
# try:
#     exp.start(port=8080, debug=False)
#     if wait_completion:
#         exp._wait_completion()
# except KeyboardInterrupt:
#     print("KeyboardInterrupt detected")
#     exp.stop()