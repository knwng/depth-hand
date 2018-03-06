import os
import numpy as np
from . import ops as dataops
from . import io as dataio
from utils.iso_boxes import iso_cube
from utils.regu_grid import latice_image


def prow_edt2m(args, thedata, batch_data):
    bi, edt2, udir2 = \
        args[0], args[1], args[2]
    edt2m = np.multiply(edt2, udir2[..., :thedata.join_num])
    batch_data[bi, ...] = edt2m


def prow_edt2(args, thedata, batch_data):
    bi, clean, poses, resce = \
        args[0], args[1], args[2], args[3]
    cube = iso_cube()
    cube.load(resce)
    edt2 = dataops.prop_edt2(
        clean, poses.reshape(-1, 3), cube, thedata)
    batch_data[bi, ...] = edt2


def prow_udir2(args, thedata, batch_data):
    bi, clean, poses, resce, = \
        args[0], args[1], args[2], args[3]
    cube = iso_cube()
    cube.load(resce)
    udir2 = dataops.raw_to_udir2(
        clean, poses.reshape(-1, 3), cube, thedata)
    batch_data[bi, ...] = udir2


def prow_ortho3(args, thedata, batch_data):
    bi, index, resce = \
        args[0], args[1], args[2]
    img_name = dataio.index2imagename(index)
    img = dataio.read_image(os.path.join(
        thedata.training_images, img_name))
    cube = iso_cube()
    cube.load(resce)
    img_ortho3 = dataops.to_ortho3(img, cube, thedata)
    batch_data[bi, ...] = img_ortho3


def prow_pose_c(args, thedata, batch_data):
    bi, poses, resce, = \
        args[0], args[1], args[2]
    cube = iso_cube()
    cube.load(resce)
    pose_c = cube.transform_to_center(
        poses.reshape(-1, 3))
    batch_data[bi, ...] = pose_c.flatten()


def prow_crop2(args, thedata, batch_data):
    bi, index, resce = \
        args[0], args[1], args[2]
    img_name = dataio.index2imagename(index)
    img = dataio.read_image(os.path.join(
        thedata.training_images, img_name))
    cube = iso_cube()
    cube.load(resce)
    img_crop2 = dataops.to_crop2(img, cube, thedata)
    batch_data[bi, ...] = img_crop2


def prow_clean(args, thedata, batch_data):
    bi, index, resce = \
        args[0], args[1], args[2]
    img_name = dataio.index2imagename(index)
    img = dataio.read_image(os.path.join(
        thedata.training_images, img_name))
    cube = iso_cube()
    cube.load(resce)
    img_clean = dataops.to_clean(img, cube, thedata)
    batch_data[bi, ...] = img_clean


def prow_index(args, thedata, batch_data):
    bi, index, poses = \
        args[0], args[1], args[2]
    pose_raw = poses.reshape(-1, 3)
    # pose_raw[:, [0, 1]] = pose_raw[:, [1, 0]]
    pose2d = dataops.raw_to_2d(pose_raw, thedata)
    if (0 > np.min(pose2d)) or (0 > np.min(thedata.image_size - pose2d)):
        return
    cube = iso_cube(
        (np.max(pose_raw, axis=0) + np.min(pose_raw, axis=0)) / 2,
        thedata.region_size
    )
    batch_data['valid'][bi] = True
    batch_data['index'][bi, ...] = index
    batch_data['poses'][bi, ...] = pose_raw
    batch_data['resce'][bi, ...] = cube.dump()


def test_puttensor(
        args, put_worker, thedata, batch_data):
    from itertools import izip
    import copy
    test_copy = copy.deepcopy(batch_data)
    for args in izip(*args):
        put_worker(
            args, thedata, batch_data)
    print('this is TEST only!!! DO NOT forget to write using mp version')
    return test_copy


def puttensor_mt(args, put_worker, thedata, batch_data):
    # from timeit import default_timer as timer
    # from datetime import timedelta
    # time_s = timer()
    # test_copy = test_puttensor(
    #     args, put_worker, thedata, batch_data)
    # time_e = str(timedelta(seconds=timer() - time_s))
    # print('single tread time: {}'.format(time_e))
    # return

    from functools import partial
    from multiprocessing.dummy import Pool as ThreadPool
    # time_s = timer()
    thread_pool = ThreadPool()
    thread_pool.map(
        partial(put_worker, thedata=thedata, batch_data=batch_data),
        zip(*args))
    thread_pool.close()  # that's it for this batch
    thread_pool.join()  # serilization point
    # time_e = str(timedelta(seconds=timer() - time_s))
    # print('multiprocessing time: {:.4f}'.format(time_e))

    # import numpy as np
    # print(np.linalg.norm(batch_data.batch_index - test_copy.batch_index))
    # print(np.linalg.norm(batch_data.batch_frame - test_copy.batch_frame))
    # print(np.linalg.norm(batch_data.batch_poses - test_copy.batch_poses))
    # print(np.linalg.norm(batch_data.batch_resce - test_copy.batch_resce))
