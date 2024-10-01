# Copyright (c) 2022-2024, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
import math
from omni.isaac.lab.managers import EventTermCfg as EventTerm
from omni.isaac.lab.managers import RewardTermCfg as RewTerm
from omni.isaac.lab.managers import SceneEntityCfg
from omni.isaac.lab.managers import TerminationTermCfg as DoneTerm
from omni.isaac.lab.managers import ObservationGroupCfg as ObsGroup
from omni.isaac.lab.managers import ObservationTermCfg as ObsTerm
from omni.isaac.lab.utils.noise import AdditiveUniformNoiseCfg as Unoise
from omni.isaac.lab.utils import configclass

from omni.isaac.lab.terrains import TerrainImporterCfg
import omni.isaac.lab.terrains as terrain_gen
from omni.isaac.lab.terrains.terrain_generator_cfg import TerrainGeneratorCfg
from omni.isaac.lab.terrains.config.rough import ROUGH_TERRAINS_CFG
import omni.isaac.lab.sim as sim_utils
from omni.isaac.lab.utils.assets import ISAAC_NUCLEUS_DIR, ISAACLAB_NUCLEUS_DIR

import omni.isaac.lab_tasks.manager_based.locomotion.velocity.mdp as mdp
from omni.isaac.lab_tasks.manager_based.locomotion.velocity.velocity_env_cfg import (
    LocomotionVelocityRoughEnvCfg,
    RewardsCfg, # type: ignore
)
from omni.isaac.lab.envs.common import ViewerCfg

from . import mdp as custom_mdp

##
# Pre-defined configs
##
from ...lab_assets import LEG10_CFG

from . import terrain
from omni.isaac.lab.managers import CurriculumTermCfg as CurrTerm

@configclass
class CurriculumCfg:
    """Curriculum terms for the MDP."""
    terrain_levels = CurrTerm(func=mdp.terrain_levels_vel) #type: ignore

@configclass
class CommandsCfg:
    """Command specifications for the MDP."""

    base_velocity = mdp.UniformVelocityCommandCfg(
        asset_name="robot",
        resampling_time_range=(5.0, 5.0),
        rel_standing_envs=0.02,
        rel_heading_envs=1.0,
        heading_command=False,
        heading_control_stiffness=0.5,
        debug_vis=False,
        ranges=mdp.UniformVelocityCommandCfg.Ranges(
            lin_vel_x=(0.0, 1.0), lin_vel_y=(-0.0, 0.0), ang_vel_z=(-1.0, 1.0), heading=(-0.0, 0.0)
        ),
    )

@configclass
class EventCfg:
    reset_base = EventTerm(
        func=mdp.reset_root_state_uniform,
        mode="reset",
        params={
            "pose_range": {
                "x": (-0.0, 0.0), 
                "y": (-0.0, 0.0),  
                "roll": (-math.pi/10, math.pi/10),
                "pitch": (-math.pi/10, math.pi/10),
                "yaw": (-math.pi/10, math.pi/10)
            },
            "velocity_range": {
                "x": (-0.5, 0.5),
                "y": (-0.5, 0.5),
                "z": (-0.5, 0.5),
                "roll": (-0.5, 0.5),
                "pitch": (-0.5, 0.5),
                "yaw": (-0.5, 0.5),
            },  
        },
    )

    reset_robot_joints = EventTerm(
        func=custom_mdp.reset_joints_by_offset,
        mode="reset",
        params={
            "position_range": {
                'R_hip_joint': (-0.1, 0.1),
                'R_hip2_joint': (-0.2, 0.2),
                'R_thigh_joint': (-0.2, 0.2),
                'R_calf_joint': (0.0, 0.2),
                'R_toe_joint': (-0.3, 0.3),
                'L_hip_joint': (-0.1, 0.1),
                'L_hip2_joint': (-0.2, 0.2),
                'L_thigh_joint': (-0.2, 0.2),
                'L_calf_joint': (0.0, 0.2),
                'L_toe_joint': (-0.3, 0.3),
            },
            "velocity_range": {
                'R_hip_joint': (-0.1, 0.1),
                'R_hip2_joint': (-0.1, 0.1),
                'R_thigh_joint': (-0.1, 0.1),
                'R_calf_joint': (-0.1, 0.1),
                'R_toe_joint': (-0.1, 0.1),
                'L_hip_joint': (-0.1, 0.1),
                'L_hip2_joint': (-0.1, 0.1),
                'L_thigh_joint': (-0.1, 0.1),
                'L_calf_joint': (-0.1, 0.1),
                'L_toe_joint': (-0.1, 0.1),
            }
        },
    )

    reset_phase = EventTerm(
        func=custom_mdp.reset_phase,
        mode="reset"
    )

    push_robot = EventTerm(
        func=mdp.push_by_setting_velocity,
        mode="interval",
        interval_range_s=(2.5, 2.5),
        params={"velocity_range": {"x": (-0.5, 0.5), "y": (-0.5, 0.5)}},
    )

@configclass
class ActionsCfg:
    """Action specifications for the MDP."""

    joint_pos = mdp.JointPositionActionCfg(
        asset_name="robot", 
        joint_names=[".*"], 
        scale=1.0, 
        use_default_offset=True
    )

@configclass
class ObservationsCfg:
    """Observation specifications for the MDP."""

    @configclass
    class PolicyCfg(ObsGroup):
        """Observations for policy group."""

        # observation terms (order preserved)
        height_scan = ObsTerm(
            func=mdp.height_scan,
            params={"sensor_cfg": SceneEntityCfg("height_scanner")},
            noise=Unoise(n_min=-0.1, n_max=0.1),
            clip=(-100.0, 100.0),
            scale=1./0.6565
        )
    
        base_lin_vel = ObsTerm(
            func=mdp.base_lin_vel, 
            noise=Unoise(n_min=-0.1, n_max=0.1),
            clip=(-100.0, 100.0),
            scale=2.0
        )

        base_ang_vel = ObsTerm(
            func=mdp.base_ang_vel, 
            noise=Unoise(n_min=-0.05, n_max=0.05),
            clip=(-100.0, 100.0),
            scale=0.25            
        )

        projected_gravity = ObsTerm(
            func=mdp.projected_gravity,
            noise=Unoise(n_min=-0.05, n_max=0.05),
            clip=(-100.0, 100.0),
            scale=1.0
        )

        velocity_commands = ObsTerm(func=mdp.generated_commands, params={"command_name": "base_velocity"})
        
        joint_pos = ObsTerm(
            func=mdp.joint_pos_rel, 
            noise=Unoise(n_min=-0.005, n_max=0.005),
            clip=(-100.0, 100.0),
            scale=1.0 
        )

        joint_vel = ObsTerm(
            func=mdp.joint_vel_rel, 
            noise=Unoise(n_min=-0.01, n_max=0.01),
            clip=(-100.0, 100.0),
            scale=0.05
        )

        actions = ObsTerm(func=mdp.last_action)

        #! Temporaly disabled height_scan, instead use base height

        base_height = ObsTerm(
            func=mdp.base_pos_z,
            params={
                "asset_cfg": SceneEntityCfg("robot"),
            },
            noise=Unoise(n_min=-0.1, n_max=0.1),
            clip=(-100.0, 100.0),
            scale=1./0.6565
        )

        # TODO: Add the binary contact force at the foot
        binary_foot_contact_state = ObsTerm(
            func=custom_mdp.binary_foot_contact_state,
            params={
                "contact_sensor_cfg": SceneEntityCfg("contact_forces", body_names=".*_toe"),
            },
            noise=Unoise(n_min=-0.1, n_max=0.1),
            clip=(-100.0, 100.0),
            scale=1.0
        )

        # TODO: Add clock phase
        clock_phase = ObsTerm(
            func=custom_mdp.clock_phase,
            clip=(-100.0, 100.0),
            scale=1.0
        )

        def __post_init__(self):
            self.enable_corruption = True
            self.concatenate_terms = True

    # observation groups
    policy: PolicyCfg = PolicyCfg()

@configclass
class RewardsCfg:
    """#! Baseline rewards
        Linear velocity: 10 
        Angular velocity: 5
        1st order action rate: -1e-3
        2nd order action rate: -1e-4
        Torque: -1e-4
        Torque limit: -0.01
        Joint limit: -10
        Termination: -100
        Energy consumption: -2.5e-5
    """
    track_lin_vel_xy_exp = RewTerm(
        func=mdp.track_lin_vel_xy_exp, weight=10.0, params={"command_name": "base_velocity", "std": math.sqrt(0.5)}
    )

    track_ang_vel_z_exp = RewTerm(
        func=mdp.track_ang_vel_z_exp, weight=5.0, params={"command_name": "base_velocity", "std": math.sqrt(0.5)}
    )

    #TODO: Override action_rate_l2 by action_rate_1st_order
    action_rate_1st_order = RewTerm(func=custom_mdp.action_rate_1st_order, weight=-1e-3)

    action_rate_2nd_order = RewTerm(func=custom_mdp.action_rate_2nd_order, weight=-1e-4)

    # dof_torques_l2 = RewTerm(
    #     func=mdp.joint_torques_l2, 
    #     weight=-1.0e-4,
    #     params={
    #         "asset_cfg": SceneEntityCfg(
    #                 "robot", 
    #                 joint_names=[
    #                     ".*_hip_joint",
    #                     ".*_hip2_joint",
    #                     ".*_thigh_joint",
    #                     ".*_calf_joint",
    #                     ".*_toe_joint"
    #                 ]
    #             )            
    #     }
    # )   

    dof_torques_limit = RewTerm(
        func=mdp.applied_torque_limits, 
        weight=-0.01,
        params={
            "asset_cfg": SceneEntityCfg(
                    "robot", 
                    joint_names=[
                        ".*_hip_joint",
                        ".*_hip2_joint",
                        ".*_thigh_joint",
                        ".*_calf_joint",
                        ".*_toe_joint"
                    ]
                ),
        }
    )

    dof_pos_limits = RewTerm(
        func=mdp.joint_pos_limits, weight=-10.0, 
        params={
            "asset_cfg": SceneEntityCfg(
                    "robot", 
                    joint_names=[
                        ".*_hip_joint",
                        ".*_hip2_joint",
                        ".*_thigh_joint",
                        ".*_calf_joint",
                        ".*_toe_joint"
                    ]
                )
        }
    )    

    termination_penalty = RewTerm(func=mdp.is_terminated, weight=-100.0)

    energy_consumption = RewTerm(
        func=custom_mdp.energy_consumption, weight=-2.5e-5,
        params={
            "asset_cfg": SceneEntityCfg(
                "robot",
                joint_names= [
                    ".*_hip_joint",
                    ".*_hip2_joint",
                    ".*_thigh_joint",
                    ".*_calf_joint",
                    ".*_toe_joint"
                ]
            )
        }
    )

    """
        #! Shaping rewards
        orientation: 5.0
        height: 2.0
        joint_regularization: 1.0
    """
    # orientation = RewTerm(
    #     func=custom_mdp.flat_orientation_exp, weight=5.0,
    #     params={
    #         "asset_cfg": SceneEntityCfg("robot"),
    #         "std": math.sqrt(0.5),
    #     },
    # )

    # #! Temporaly disabled height_scan, instead use base height
    # base_height = RewTerm(
    #     func=custom_mdp.base_height_exp, weight=2.0,
    #     params={
    #         "asset_cfg": SceneEntityCfg("robot"),
    #         "target_height": 0.77,
    #         "std": math.sqrt(0.5),
    #     },
    # )

    # joint_regularization = RewTerm(
    #     func=custom_mdp.joint_regulization_exp, weight=1.0,
    #     params={
    #         "asset_cfg": SceneEntityCfg("robot"),
    #         "std": math.sqrt(0.5),
    #     }
    # )

    """
        # TODO Potential-based rewards
        orientation: 1.0
        height: 1.0
        joint_regularization: 1.0
    """
    pb_orientation = RewTerm(
        func=custom_mdp.pb_flat_orientation_exp, weight=1.0,
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "std": math.sqrt(0.5),
        },
    )

    pb_base_height = RewTerm(
        func=custom_mdp.pb_base_height_exp, weight=1.0,
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "target_height": 0.78,
            "std": math.sqrt(0.5),
        },
    )

    pb_joint_regularization = RewTerm(
        func=custom_mdp.pb_joint_regulization_exp, weight=1.0,
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "std": math.sqrt(0.5),
        }
    )





@configclass
class TerminationsCfg:
    """Termination terms for the MDP."""
    base_contact = DoneTerm(
        func=mdp.illegal_contact,
        params={"sensor_cfg": SceneEntityCfg("contact_forces", body_names=["base", "R_thigh", "R_calf", "L_thigh", "L_calf"]), "threshold": 1.0},
    )

    bad_orientation = DoneTerm(
        func=custom_mdp.my_bad_orientation,
        params={
            "asset_cfg": SceneEntityCfg("robot"),
            "limit_gx": 0.7,
            'limit_gy': 0.7
        },
    )

    time_out = DoneTerm(func=mdp.time_out, time_out=True) 

    norm_base_lin_vel_out_of_limit = DoneTerm(
        func=custom_mdp.norm_base_lin_vel_out_of_limit, 
        params={
            "max_norm": 10.0,
            "asset_cfg": SceneEntityCfg("robot"),    
        }
    )

    norm_base_ang_vel_out_of_limit = DoneTerm(
        func=custom_mdp.norm_base_ang_vel_out_of_limit,
        params={
            "max_norm": 5.0,
            "asset_cfg": SceneEntityCfg("robot"),
        }
    )




@configclass
class LegRobotParkourEnvCfg(LocomotionVelocityRoughEnvCfg):
    
    commands: CommandsCfg = CommandsCfg()
    events: EventCfg = EventCfg()
    actions: ActionsCfg = ActionsCfg()
    rewards: RewardsCfg = RewardsCfg()
    terminations: TerminationsCfg = TerminationsCfg()
    curriculum: CurriculumCfg = CurriculumCfg()
    observations: ObservationsCfg = ObservationsCfg()

    def __post_init__(self):
        # post init of parent
        super().__post_init__()

        # general settings
        self.decimation = 10
        self.episode_length_s = 5.0

        # simulation settings
        self.sim.dt = 0.001
        self.sim.render_interval = self.decimation
        self.sim.physx.min_position_iteration_count = 4
        self.sim.physx.max_position_iteration_count = 4
        self.sim.physx.min_velocity_iteration_count = 0
        self.sim.physx.max_velocity_iteration_count = 0

        # Scene
        self.scene.robot = LEG10_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot") # type: ignore
        self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base"
        
        # TODO: Define the terrain
        PARKOUR_TERRAINS_CFG = TerrainGeneratorCfg(
            size=(10.0, 10.0),
            border_width=20.0,
            num_rows=5,
            num_cols=1,
            horizontal_scale=0.1,
            vertical_scale=0.005,
            slope_threshold=0.75,
            use_cache=False,
            sub_terrains={
                # "random_rough": terrain_gen.HfRandomUniformTerrainCfg(
                #     proportion=0.2, noise_range=(0.00, 0.03), noise_step=0.02, border_width=0.0
                # ),
            #    "hurdle_with_rough": terrain_gen.trimesh.mesh_terrains_cfg.MeshBoxTerrainCfg(
            #         box_height_range=(0.05, 0.5), platform_width=0.1
            #     ),
                "hurdle_noise": terrain.HurdleNoiseTerrainCfg(
                    box_height_range=(0.05, 0.5), platform_width=(0.1, 10.0), box_position=(1.0, 0.0),
                    random_uniform_terrain_cfg=terrain_gen.HfRandomUniformTerrainCfg(
                        proportion=0.2, noise_range=(0.00, 0.011), noise_step=0.01, border_width=0.0,
                        size=(10.0, 10.0),
                    )
                )
            }, #type: ignore
            curriculum=True,
        )

        self.scene.terrain = TerrainImporterCfg(
            prim_path="/World/ground",
            terrain_type="generator",
            terrain_generator=PARKOUR_TERRAINS_CFG,
            max_init_terrain_level=5,
            collision_group=-1,
            physics_material=sim_utils.RigidBodyMaterialCfg(
                friction_combine_mode="multiply",
                restitution_combine_mode="multiply",
                static_friction=1.0,
                dynamic_friction=1.0,
            ),
            visual_material=sim_utils.MdlFileCfg(
                mdl_path=f"{ISAACLAB_NUCLEUS_DIR}/Materials/TilesMarbleSpiderWhiteBrickBondHoned/TilesMarbleSpiderWhiteBrickBondHoned.mdl",
                project_uvw=True,
                texture_scale=(0.25, 0.25),
            ),
            debug_vis=False,
        )

        # self.scene.env_spacing = 0.0

        # TODO: Customize heigh scanner
        from omni.isaac.lab.sensors.ray_caster.patterns.patterns_cfg import GridPatternCfg
        self.scene.height_scanner.debug_vis = False
        self.scene.height_scanner.pattern_cfg = GridPatternCfg(resolution=0.1, size=(1.6, 1.0))
        # self.scene.terrain.terrain_type = "plane"
        # self.scene.terrain.terrain_generator = None


        #! Just for debug purposes
        #! Should be commented out when actually trainning
        # self.viewer = ViewerCfg(
        #     eye=(3, 3, 3),
        #     origin_type='asset_root',
        #     asset_name='robot',
        #     env_index=0,
        # )



@configclass
class LegRobotParkourEnvCfg_PLAY(LegRobotParkourEnvCfg):
    def __post_init__(self):
        # post init of parent
        super().__post_init__()


        # self.scene.terrain = TerrainImporterCfg(
        #     prim_path="/World/ground",
        #     terrain_type="generator",
        #     terrain_generator=ROUGH_TERRAINS_CFG,
        #     max_init_terrain_level=5,
        #     collision_group=-1,
        #     physics_material=sim_utils.RigidBodyMaterialCfg(
        #         friction_combine_mode="multiply",
        #         restitution_combine_mode="multiply",
        #         static_friction=1.0,
        #         dynamic_friction=1.0,
        #     ),
        #     visual_material=sim_utils.MdlFileCfg(
        #         mdl_path=f"{ISAACLAB_NUCLEUS_DIR}/Materials/TilesMarbleSpiderWhiteBrickBondHoned/TilesMarbleSpiderWhiteBrickBondHoned.mdl",
        #         project_uvw=True,
        #         texture_scale=(0.25, 0.25),
        #     ),
        #     debug_vis=False,
        # )


        # self.scene.num_envs = 1
        # self.scene.env_spacing = 2.5
        # self.episode_length_s = 20.0

        # self.scene.terrain.max_init_terrain_level = 1
        # # reduce the number of terrains to save memory
        # if self.scene.terrain.terrain_generator is not None:
        #     self.scene.terrain.terrain_generator.num_rows = 5
        #     self.scene.terrain.terrain_generator.num_cols = 5

        #     self.scene.terrain.terrain_generator.curriculum = True
        #     self.scene.terrain.num_envs = self.scene.num_envs
        #     self.scene.terrain.debug_vis = True

        #     self.scene.terrain.terrain_generator.sub_terrains["pyramid_stairs"].step_height_range = (0.01, 0.05) #type: ignore
        #     self.scene.terrain.terrain_generator.sub_terrains["pyramid_stairs_inv"].step_height_range = (0.01, 0.05) #type: ignore
        #     self.scene.terrain.terrain_generator.sub_terrains["boxes"].grid_height_range = (0.01, 0.02) #type: ignore
        #     self.scene.terrain.terrain_generator.sub_terrains["random_rough"].noise_range = (0.01, 0.02) #type: ignore

        self.commands.base_velocity.ranges.lin_vel_x = (0.0, 0.8)
        self.commands.base_velocity.ranges.lin_vel_y = (0.0, 0.0)
        self.commands.base_velocity.ranges.ang_vel_z = (-0.5, 0.5)
        self.commands.base_velocity.debug_vis = True

        # disable randomization for play
        self.observations.policy.enable_corruption = False
        # remove random pushing
        self.events.base_external_force_torque = None # type: ignore
        self.events.push_robot = None # type: ignore

        #! Just for debug purposes
        #! Should be commented out when actually trainning
        self.scene.height_scanner.debug_vis = True
        # self.viewer = ViewerCfg(
        #     eye=(3, 3, 3),
        #     origin_type='asset_root',
        #     asset_name='robot',
        #     env_index=0,
        # )

        # self.sim.render_interval = self.decimation * 2
        self.scene.contact_forces.debug_vis = False
 