#!/bin/sh
#
# Copyright (C) 2005-2019 Centre National d'Etudes Spatiales (CNES)
#
# This file is part of Orfeo Toolbox
#
#     https://www.orfeo-toolbox.org/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
set -e
rm -fr /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/include/OTB-*
rm -f /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/lib/{libotb*,libOTB*}
rm -fr /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/lib/{otb,python/*otbApplication*}
rm -fr /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/lib/cmake/OTB-*
rm -fr /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/share/otb/
rm -fv /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/bin/{otb*,monteverdi,mapla}
rm -fv /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/{mapla.sh,monteverdi.sh}
rm -fv /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64/otbenv.*

echo "OTB is now uninstalled from /home/innopam-ldm/PycharmProjects/Orthophoto_Maps_multiSpectral/OTB-7.0.0-Linux64"
