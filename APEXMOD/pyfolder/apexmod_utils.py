import numpy as np
import datetime
import os

class ObjFns:
    def __init__(self) -> None:
        pass
        
    # def obj_fns(obj_fn, sims, obds):
    #     return obj_fn(sims, obds)
    @staticmethod
    def nse(sims, obds):
        """Nash-Sutcliffe Efficiency (NSE) as per `Nash and Sutcliffe, 1970
        <https://doi.org/10.1016/0022-1694(70)90255-6>`_.

        :Calculation Details:
            .. math::
            E_{\\text{NSE}} = 1 - \\frac{\\sum_{i=1}^{N}[e_{i}-s_{i}]^2}
            {\\sum_{i=1}^{N}[e_{i}-\\mu(e)]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series, and *μ* is the arithmetic mean.

        """
        nse_ = 1 - (
                np.sum((obds - sims) ** 2, axis=0, dtype=np.float64)
                / np.sum((obds - np.mean(obds)) ** 2, dtype=np.float64)
        )
        return nse_

    @staticmethod
    def rmse(sims, obds):
        """Root Mean Square Error (RMSE).

        :Calculation Details:
            .. math::
            E_{\\text{RMSE}} = \\sqrt{\\frac{1}{N}\\sum_{i=1}^{N}[e_i-s_i]^2}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, *s* is (one of) the
            *sims* series.

        """
        rmse_ = np.sqrt(np.mean((obds - sims) ** 2,
                                axis=0, dtype=np.float64))

        return rmse_

    @staticmethod
    def pbias(sims, obds):
        """Percent Bias (PBias).

        :Calculation Details:
            .. math::
            E_{\\text{PBias}} = 100 × \\frac{\\sum_{i=1}^{N}(e_{i}-s_{i})}{\\sum_{i=1}^{N}e_{i}}

            where *N* is the length of the *sims* and *obds*
            periods, *e* is the *obds* series, and *s* is (one of)
            the *sims* series.

        """
        pbias_ = (100 * np.sum(obds - sims, axis=0, dtype=np.float64)
                / np.sum(obds))

        return pbias_

    @staticmethod
    def rsq(sims, obds):
        ## R-squared
        rsq_ = (
            (
                (sum((obds - obds.mean())*(sims-sims.mean())))**2
            ) 
            /
            (
                (sum((obds - obds.mean())**2)* (sum((sims-sims.mean())**2))
            ))
        )
        return rsq_


class DefineTime:

    def __init__(self) -> None:
        pass

    def get_start_end_time(self):
        APEXMOD_path_dict = self.dirs_and_paths()
        wd = APEXMOD_path_dict['apexmf_model']
        if os.path.isfile(os.path.join(wd, "APEXCONT.DAT")):
            with open(os.path.join(wd, 'APEXCONT.DAT'), "r") as f:
                data = [x.strip().split() for x in f if x.strip()]
            numyr = int(data[0][0])
            styr = int(data[0][1])
            stmon = int(data[0][2])
            stday = int(data[0][3])
            ptcode = int(data[0][4])
            edyr = styr + numyr -1
            stdate = datetime.datetime(styr, stmon, 1) + datetime.timedelta(stday - 1)
            eddate = datetime.datetime(edyr, 12, 31)
            duration_ = (eddate - stdate).days
            stdate_ = stdate.strftime("%m/%d/%Y")
            eddate_ = eddate.strftime("%m/%d/%Y")
            return stdate_, eddate_, duration_