#########################################################
#  ____           _                                     #
# |  _ \ ___   __| |_ __ _   _ _ __ ___                 #
# | |_) / _ \ / _` | '__| | | | '_ ` _ \                #
# |  __/ (_) | (_| | |  | |_| | | | | | |               #
# |_|   \___/ \__,_|_|   \__,_|_| |_| |_|               #
#                                                       #
# Copyright 2021 Podrum Team.                           #
#                                                       #
# This file is licensed under the GPL v2.0 license.     #
# The license file is located in the root directory     #
# of the source code. If not you may not use this file. #
#                                                       #
#########################################################

from collections import deque
import math
from podrum.block.block_map import block_map
from podrum.geometry.vector_2 import vector_2
from threading import Thread
from time import sleep
from queue import Queue
from podrum.task.immediate_task import immediate_task

class world:
    def __init__(self, provider: object, server: object):
        self.provider: object = provider
        self.server: object = server
        self.chunks: dict = {}
        self.mark_as_loading: object = deque()
        self.mark_as_saving: object = deque()
        self.mark_as_unloading: object = deque()
        self.world_path: str = provider.world_dir
        self.load_queue: object = Queue()
        self.unload_queue: object = Queue()
    
    # [load_chunk]
    # :return: = None
    # Loads a chunk.
    def load_chunk(self, x: int, z: int) -> None:
        if not self.has_loaded_chunk(x, z):
            if f"{x} {z}" not in self.mark_as_loading:
                self.mark_as_loading.append(f"{x} {z}")
                chunk: object = self.provider.get_chunk(x, z)
                if chunk is None:
                    generator: object = self.server.managers.generator_manager.get_generator(self.get_generator_name())
                    chunk: object = generator.generate(x, z, self)
                self.chunks[f"{x} {z}"] = chunk
                self.mark_as_loading.remove(f"{x} {z}")
                
    # [save_chunk]
    # :return: = None
    # Saves a chunk to its file.
    def save_chunk(self, x: int, z: int) -> None:
        if self.has_loaded_chunk(x, z):
            if f"{x} {z}" not in self.mark_as_saving:
                self.mark_as_saving.append(f"{x} {z}")
                self.provider.set_chunk(self.get_chunk(x, z))
                self.mark_as_saving.remove(f"{x} {z}")
         
    # [unload_chunk]
    # :return: = None
    # Saves and unloads a chunk.
    def unload_chunk(self, x: int, z: int) -> None:
        if f"{x} {z}" not in self.unloading:
            self.mark_as_unloading.append(f"{x} {z}")
            if f"{x} {z}" in self.mark_as_saving:
                self.save_chunk(x, z)
            while f"{x} {z}" in self.mark_as_saving:
                pass
            del self.chunks[f"{x} {z}"]
            self.mark_as_unloading.remove(f"{x} {z}")
            
    # [load_worker]
    # :return: -> None
    # The worker that loads chunks
    def load_worker(self) -> None:
        while True:
            if not self.load_queue.empty():
                item: tuple = self.load_queue.get()
                if item is None:
                    break
                self.load_chunk(item[0], item[1])
            else:
                sleep(0.05)
        
    # [start_load_workers]
    # :return: = list
    # Starts a give amount of load workers.
    def start_load_workers(self, count: int) -> list:
        workers: list = []
        self.load_worker_count: int = count
        for i in range(0, count):
            worker: object = Thread(target = self.load_worker)
            worker.start()
            workers.append(worker)
        return workers
          
    # [stop_load_workers
    # :return: = None
    # Stops the load workers
    def stop_load_workers(self) -> None:
        for i in range(0, self.load_worker_count):
            self.load_queue.put(None)
       
    # [unload_worker]
    # :return: -> None
    # The worker that unloads chunks
    def unload_worker(self) -> None:
        while True:
            if not self.unload_queue.empty():
                item: tuple = self.unload_queue.get()
                if item is None:
                    break
                self.unload_chunk(item[0], item[1])
            else:
                sleep(0.05)
                
    # [start_load_workers]
    # :return: = list
    # Starts a give amount of load workers.
    def start_unload_workers(self, count: int) -> list:
        workers: list = []
        self.unload_worker_count: int = count
        for i in range(0, count):
            worker: object = Thread(target = self.unload_worker)
            worker.start()
            workers.append(worker)
        return workers
          
    # [stop_load_workers
    # :return: = None
    # Stops the load workers
    def stop_unload_workers(self) -> None:
        for i in range(0, self.unload_worker_count):
            self.unload_queue.put(None)

    # [has_loaded_chunk]
    # :return: = bool
    # Checks if a chunk is loaded.
    def has_loaded_chunk(self, x: int, z: int) -> bool:
        if f"{x} {z}" in self.chunks:
            return True
        return False
    
    # [get_chunk]
    # :return: = object
    # Gets a chunk.
    def get_chunk(self, x: int, z: int) -> object:
        return self.chunks[f"{x} {z}"]
    
    # [get_block]
    # :return: = None
    # Gets a block.
    def get_block(self, x: int, y: int, z: int) -> None:
        block_and_meta: tuple = block_map.get_name_and_meta(self.chunks[f"{x >> 4} {z >> 4}"].get_block_runtime_id(x & 0x0f, y & 0x0f, z & 0x0f))
        return self.server.managers.block_manager.get_block(block_and_meta[0], block_and_meta[1])
    
    # [set_block]
    # :return: = None
    # Sets a block.
    def set_block(self, x: int, y: int, z: int, block: object) -> None:
        self.chunks[f"{x >> 4} {z >> 4}"].set_block_runtime_id(x & 0x0f, y & 0x0f, z & 0x0f, block.runtime_id)
        
    # [get_highest_block_at]
    # :return: = int
    # Get the highest block y position.
    def get_highest_block_at(self, x: int, z: int) -> int:
        return self.chunks[f"{x >> 4} {z >> 4}"].get_highest_block_at(x & 0x0f, z & 0x0f)
    
    # [save]
    # :return: = None
    # Saves the world.
    def save(self) -> None:
        tasks: list = []
        for chunk in self.chunks.values():
            chunk_task: object = Thread(target = self.save_chunk, args = [chunk.x, chunk.z])
            chunk_task.start()
            tasks.append(chunk_task)
        for task in tasks:
            task.join()
    
    # [get_world_name]
    # :return: = str
    # Gets a world name.
    def get_world_name(self) -> str:
        return self.provider.get_world_name()
    
    # [set_world_name]
    # :return: = None
    # Sets a world name.
    def set_world_name(self, world_name: str) -> None:
        self.provider.set_world_name(world_name)
        
    # [get_spawn_position]
    # :return: = object
    # Gets the world spawn position.
    def get_spawn_position(self) -> object:
        return self.provider.get_spawn_position()
    
    # [set_spawn_position]
    # :return: = None
    # Sets a spawn position.
    def set_spawn_position(self, world_name: object) -> None:
        self.provider.set_spawn_position(world_name)

    # [get_world_gamemode]
    # :return: = None
    # Gets the world's default generator.
    def get_world_gamemode(self) -> str:
        return self.provider.get_world_gamemode()
        
    # [set_world_gamemode]
    # :return: = None
    # Sets the default world gamemode.
    def set_world_gamemode(self, world_name: str) -> None:
        self.provider.set_world_gamemode(world_name)
        
    # [get_player_position]
    # :return: = object
    # Gets a vector_3 that contains a player's
    # current position.
    def get_player_position(self, uuid: str) -> object:
        return self.provider.get_player_position(uuid)
        
    # [set_player_position]
    # :return: = None
    # Sets a player's default position.
    def set_player_position(self, uuid: str, position: object) -> None:
        self.provider.set_player_position(uuid, position)

    # [get_player_gamemode]
    # :return: = int
    # Gets player gamemode.
    def get_player_gamemode(self, uuid: str) -> int:
        return self.provider.get_player_gamemode(uuid)
        
    # [set_player_gamemode]
    # :return: = None
    # Sets a player's gamemode.
    def set_player_gamemode(self, uuid: str, gamemode: int) -> None:
        self.provider.set_player_gamemode(uuid, gamemode)
        
    # [create_player]
    # :return: = None
    # Creates a new player file.
    def create_player(self, uuid: str) -> None:
        self.provider.create_player_file(uuid)
        
    # [has_player]
    # :return: = bool
    # Checks if a player exists.
    def has_player(self, uuid: str) -> bool:
        return self.provider.has_player_file(uuid)
        
    # [get_generator_name]
    # :return: = None
    # Gets the default generator name.
    def get_generator_name(self) -> str:
        return self.provider.get_generator_name()
    
    # [set_generator_name]
    # :return: = None
    # Sets the default generator name.
    def set_generator_name(self, generator_name: str) -> None:
        self.provider.set_generator_name(generator_name)
